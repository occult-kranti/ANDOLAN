import './lab.css';
import { HEROES, heroById } from '../shared/heroes';
import { SOLIDS, SPAWNS, distance } from '../shared/map';
import { UPGRADE_COSTS, MAX_UPGRADE, ARENA_RULES } from '../shared/simulation';
import type { Actor, ArenaInput } from '../shared/types';
import { createArenaWorld, type ArenaWorld } from '../client/world';
import { ArenaAudio } from '../client/audio';
import { acquireTarget, targetAim } from '../client/targeting';
import { waitForRenderedFrames } from '../client/render-warmup';
import { ReferenceLab, REFERENCE_EXPERIMENTS, REFERENCE_RULES, CONTROL_RULES, type ReferenceExperiment, type ReferenceSnapshot, type ReferenceCommand } from '../reference/controller';
import { objectiveStatus } from './objective-status';

const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;
const escape = (value: string) => value.replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]!));
const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
type Preferences = { quality: 'low' | 'high'; lighting: 'cycle' | 'day' | 'night'; reducedMotion: boolean; sensitivity: number; sound: boolean };
const preferences: Preferences = { quality: 'high', lighting: 'day', reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches, sensitivity: 1, sound: false };
try {
  const saved = JSON.parse(localStorage.getItem('yuga.reference.preferences.v1') || '{}');
  preferences.quality = saved.quality === 'low' ? 'low' : 'high';
  preferences.lighting = saved.lighting === 'night' || saved.lighting === 'cycle' ? saved.lighting : 'day';
  if (typeof saved.reducedMotion === 'boolean') preferences.reducedMotion = saved.reducedMotion;
  if (Number.isFinite(saved.sensitivity)) preferences.sensitivity = clamp(saved.sensitivity, .3, 2);
  preferences.sound = saved.sound === true;
} catch { /* Storage is optional. */ }
const configuredTrack: unknown = import.meta.env.VITE_YUGA_LAB_TRACK;
const track = configuredTrack === 'lane' || configuredTrack === 'control' ? configuredTrack : 'all';
let experiment: ReferenceExperiment = track === 'control' ? 'control-point' : 'lane-economy';
let selected = HEROES[0]!;
let lab: ReferenceLab | undefined, state: ReferenceSnapshot | undefined, world: ArenaWorld | undefined, creatingWorld: Promise<ArenaWorld> | undefined;
let playing = false, ready = false, loading = false, ended = false, destroyed = false, generation = 0;
let loadAbort: AbortController | undefined, activeDialog: HTMLDialogElement | undefined, priorFocus: HTMLElement | null = null;
let yaw = 0, pitch = .02, seq = 0, commandSerial = 0, aimTarget: string | null = null;
let inputAt = performance.now(), frameAt = performance.now(), lastHud = 0, lastEvent = -1, lastReceipt = -1, toastUntil = 0, hitUntil = 0;
let warmFrames = 0, renderedFrames = 0, inputSeconds = 0, lastResult: { ok: boolean; code: string } | null = null;
const held = new Set<string>(), touchHeld = new Set<string>();
let mousePointer: number | null = null, lookPointer: number | null = null, pointerFire = false, touchFire = false, dragging = false, lastX = 0, lastY = 0;
const audio = new ArenaAudio();

$('app').innerHTML = `
<main id="lab-lobby">
 <div class="lobby-art" aria-hidden="true"></div>
 <header class="masthead"><a class="brand" href="../">YUGA<small>CONFLUENCE · MECHANICS LAB</small></a><span id="lab-track-label" class="edition">${track === 'lane' ? 'LANE ECONOMY TRACK' : track === 'control' ? 'HYBRID CONTROL TRACK' : 'ORIGINAL PLAYABLE EXPERIMENTS'} · v1</span><button id="lab-lobby-settings" class="quiet">Settings</button></header>
 <section class="lab-intro"><p class="eyebrow">PLAY · OBSERVE · RESTART</p><h1>${track === 'lane' ? 'Earn an edge.<br>Lead the push.' : track === 'control' ? 'Take the court.<br>Hold your ground.' : 'One city.<br>Two ways to win.'}</h1><p>${track === 'all' ? 'Compare a lane economy with a hybrid control point.' : track === 'lane' ? 'Trace income, upgrades and a three-lane push.' : 'Contest a central control point inside a living lane battle.'} Take the field with five bots, using YUGA’s original heroes and arena.</p></section>
 <p id="lab-error" class="entry-error" role="alert" hidden></p>
 <div class="lab-layout"><section aria-label="Choose an experiment">
  <div class="experiment-list">
   <button class="experiment" data-experiment="lane-economy" aria-pressed="true"><span class="number">01</span><span><strong>Three-lane economy</strong><small>Earn together. Contest shards. Upgrade at base.<br>Push through two towers to the rival core.</small></span><svg viewBox="0 0 50 60" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2"><path d="M25 4 8 16v28l17 12m0-52v52m0-52 17 12v28L25 56"/><circle cx="25" cy="4" r="3" fill="currentColor"/><circle cx="25" cy="56" r="3" fill="currentColor"/></svg></button>
   <button class="experiment" data-experiment="control-point" aria-pressed="false"><span class="number">02</span><span><strong>Hybrid team control</strong><small>Capture the central court. Stay to score.<br>The surrounding lane battle keeps running.</small></span><svg viewBox="0 0 50 60" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2"><circle cx="25" cy="30" r="19"/><circle cx="25" cy="30" r="10"/><path d="M25 2v13m0 30v13M0 30h11m28 0h11"/><path d="m25 24 6 6-6 6-6-6z" fill="currentColor"/></svg></button>
  </div>
  <div class="experiment-details"><h3 id="lab-rule-title"></h3><ul id="lab-rule-copy"></ul></div>
  <details class="entry-help"><summary>Controls and what the lab measures</summary><p><kbd>W A S D</kbd> move · mouse drag or <kbd>I J K L</kbd> aim · click or <kbd>F</kbd> fire · <kbd>Q E R</kbd> abilities · <kbd>X</kbd> reload · <kbd>Space</kbd> jump.</p><p>Each primary weapon has ${REFERENCE_RULES.magazine} rounds and a ${REFERENCE_RULES.reloadSeconds}-second reload in this lab. Abilities use cooldowns. Wallet receipts record actual income and purchases; a single run is an observation, not a balance verdict.</p></details>
 </section>
 <section class="hero-setup" aria-label="Set up your run"><label class="field-label" for="lab-hero">YOUR HERO · ALL ${HEROES.length} AVAILABLE</label><select id="lab-hero">${HEROES.map(hero => `<option value="${hero.id}">${escape(hero.name)} · ${hero.role}</option>`).join('')}</select><h2 id="lab-hero-name" class="hero-name"></h2><p id="lab-hero-role" class="hero-role"></p><p id="lab-hero-description" class="hero-description"></p><div id="lab-kit" class="kit-summary"></div><div class="seed-field"><label class="field-label" for="lab-seed">Run seed<small>Reuse to compare the same bot roster.</small></label><input id="lab-seed" type="number" inputmode="numeric" min="0" max="4294967295" step="1" value="7301"></div><button id="lab-launch" class="primary">Launch lane experiment</button><p class="local-note">Runs locally · No account or server required</p></section>
 </div><footer class="lab-footer"><span>Original reference implementations, not complete Deadlock or Overwatch replicas.</span><nav aria-label="Lab editions"><a href="../lab/"${track === 'all' ? ' aria-current="page"' : ''}>Both experiments</a> · <a href="../lane-lab/"${track === 'lane' ? ' aria-current="page"' : ''}>Lane track</a> · <a href="../control-lab/"${track === 'control' ? ' aria-current="page"' : ''}>Control track</a></nav><span>Background: illustrated YUGA concept art · <a href="../">Return to YUGA</a></span></footer>
</main>
<canvas id="lab-canvas" tabindex="0" aria-label="Mechanics lab arena. WASD move, IJKL aim, F fires, QER abilities, X reloads, Space jumps, T locks a target, Escape pauses." hidden></canvas>
<section id="lab-hud" aria-label="Experiment heads-up display" hidden>
 <svg id="lab-point-ring" aria-hidden="true" hidden>${Array.from({ length: 40 }, () => '<line/>').join('')}</svg><div id="lab-point-beacon" hidden>CONTROL COURT<span></span></div>
 <div class="scoreboard"><div class="score"><small>YOUR TEAM</small><strong id="lab-score-sun">0</strong></div><div class="score-center"><p id="lab-mode" class="eyebrow"></p><div id="lab-clock" class="clock">8:00</div><p id="lab-objective"></p></div><div class="score rivals"><small>RIVALS</small><strong id="lab-score-moon">0</strong></div></div>
 <div class="match-tools"><button id="lab-help" class="quiet">Controls</button><button id="lab-pause" class="quiet">Pause <kbd>Esc</kbd></button></div>
 <div class="map-panel"><canvas id="lab-map" width="258" height="314" aria-label="Arena minimap. Circles are allies, diamonds are rivals; the central ring is the control court."></canvas><small id="lab-map-caption">GHAT · TEMPLE · METRO</small></div>
 <div id="lab-point" class="point-panel" hidden><strong id="lab-point-owner">Unclaimed court</strong><small id="lab-point-occupants"></small><div class="point-track"><i id="lab-point-progress"></i></div><small id="lab-point-contested"></small></div>
 <aside class="match-readout" aria-label="Run observations"><strong>THIS RUN · OBSERVED</strong><p id="lab-economy-total">Earned 0 · Spent 0</p><ul id="lab-receipts"><li>No wallet changes yet.</li></ul></aside>
 <div id="lab-reticle" aria-hidden="true" hidden></div><div id="lab-target" hidden></div><div id="lab-toast" role="status" aria-live="polite" hidden></div><div id="lab-respawn" hidden></div>
 <div class="bottom-hud"><div class="vitals"><strong id="lab-vitals-name"></strong><p id="lab-health"></p><div class="health-track"><i id="lab-health-fill"></i></div><small id="lab-record"></small></div><div class="abilities">${[0, 1, 2].map((slot) => `<button class="ability" data-ability="${slot}"><kbd>${['Q', 'E', 'R'][slot]}</kbd><strong></strong><span>Ready</span></button>`).join('')}</div><div class="weapon"><strong id="lab-ammo">12 / 12</strong><small id="lab-reload-status">PRIMARY WEAPON</small><button id="lab-reload">Reload <kbd>X</kbd></button></div><div class="wallet"><strong id="lab-credits">180</strong><small>CREDITS</small><button id="lab-forge">Upgrade <kbd>B</kbd></button></div></div>
 <p class="control-strip">WASD move · Drag / IJKL aim · Click / F fire · T target lock · QER abilities · X reload · Space jump</p>
 <div class="touch-controls"><div class="dpad" aria-label="Move"><button data-touch-key="KeyW" aria-label="Move forward">↑</button><button data-touch-key="KeyA" aria-label="Move left">←</button><button data-touch-key="KeyS" aria-label="Move back">↓</button><button data-touch-key="KeyD" aria-label="Move right">→</button></div><div><p class="touch-note">Drag the arena to aim</p><div class="touch-actions"><button id="lab-touch-target">Lock target</button><button data-touch-key="Space">Jump</button><button id="lab-touch-fire">Fire</button></div></div></div>
</section>
<dialog id="lab-settings-dialog" aria-labelledby="lab-settings-title"><p class="eyebrow">LOCAL PREFERENCES</p><h2 id="lab-settings-title">Pause & settings</h2><p id="lab-pause-copy">Your preferences are saved on this device.</p><div class="settings-grid"><label for="lab-quality">Visual quality<select id="lab-quality"><option value="high">High · shadows & stars</option><option value="low">Low · lighter rendering</option></select></label><label for="lab-lighting">Lighting<select id="lab-lighting"><option value="day">Fixed day</option><option value="night">Fixed night</option><option value="cycle">480-second cycle</option></select></label><label for="lab-sensitivity">Aim sensitivity <output id="lab-sensitivity-value">1.0×</output><input id="lab-sensitivity" type="range" min="30" max="200" value="100"></label><button id="lab-sound-preview">Preview sound</button><label class="check"><input id="lab-reduced-motion" type="checkbox">Reduce decorative motion</label><label class="check"><input id="lab-sound" type="checkbox">Enable original game audio</label></div><p id="lab-audio-status"></p><div class="dialog-actions"><button id="lab-resume" class="primary">Done</button><button id="lab-restart" hidden>Restart this run</button><button id="lab-back" class="danger" hidden>Back to experiments</button></div></dialog>
<dialog id="lab-controls-dialog" aria-labelledby="lab-controls-title"><p class="eyebrow">YOUR RUN IS PAUSED</p><h2 id="lab-controls-title">Take the field</h2><p>Aim with a mouse drag or the keyboard. Target lock helps keep a visible enemy in view; cover still blocks shots.</p><div class="help-grid"><span>Move</span><b>W A S D / arrow keys</b><span>Aim</span><b>Drag / I J K L</b><span>Primary fire</span><b>Click / F</b><span>Three abilities</span><b>Q / E / R</b><span>Reload primary</span><b>X</b><span>Jump</span><b>Space</b><span>Toggle target lock</span><b>T / right click</b><span>Upgrade at base</span><b>B</b><span>Pause</span><b>Escape</b></div><p>On touch screens, use the direction pad, drag the arena to aim, and tap the visible action controls.</p><div class="dialog-actions"><button data-close class="primary">Resume run</button></div></dialog>
<dialog id="lab-forge-dialog" aria-labelledby="lab-forge-title"><p class="eyebrow">SPEND OBSERVED INCOME</p><h2 id="lab-forge-title">Base upgrades</h2><p>Time is paused here. Purchases are available near your own base and produce a wallet receipt.</p><p id="lab-forge-balance"></p><div class="forge-list">${(['power', 'vitality', 'tempo'] as const).map(kind => `<button data-upgrade="${kind}"><span><strong>${kind[0]!.toUpperCase() + kind.slice(1)}</strong><small>${kind === 'power' ? 'Increase primary and ability damage.' : kind === 'vitality' ? 'Increase maximum health by 65 each rank.' : 'Shorten primary-fire recovery.'}</small></span><b></b></button>`).join('')}</div><p id="lab-forge-result" role="status"></p><div class="dialog-actions"><button data-close class="primary">Resume run</button></div></dialog>
<dialog id="lab-result-dialog" aria-labelledby="lab-result-title"><p class="eyebrow">RUN COMPLETE</p><h2 id="lab-result-title"></h2><p id="lab-result-reason"></p><p id="lab-result-summary"></p><table class="result-table"><thead><tr><th>Hero</th><th>K / A / D</th><th>Credits</th></tr></thead><tbody id="lab-results"></tbody></table><p>Same seed preserves the bot roster. Your actions and the chosen objective can produce a different result.</p><div class="dialog-actions"><button id="lab-result-restart" class="primary">Repeat this run</button><button id="lab-result-back">Choose an experiment</button></div></dialog>
<section id="lab-loading" role="status" aria-live="polite" hidden><div class="load-mark" aria-hidden="true"><span>Y</span></div><h2>Preparing your run</h2><p id="lab-loading-copy">Loading the arena…</p><small>The clock starts after the actual scene has rendered. First use downloads the original 3D assets.</small><button id="lab-loading-back">Back to experiments</button></section>`;

const canvas = $<HTMLCanvasElement>('lab-canvas');
const pointRing = document.querySelector<SVGSVGElement>('#lab-point-ring')!;
const pointLines = [...document.querySelectorAll<SVGLineElement>('#lab-point-ring line')];
const active = () => playing && ready && !loading && !ended && !activeDialog && !document.hidden;
const me = (): Actor | undefined => state?.arena.actors.find(actor => actor.id === state?.localId);
const pressed = (code: string) => held.has(code) || touchHeld.has(code);
function notify(message: string) { $('lab-toast').textContent = message; $('lab-toast').hidden = false; toastUntil = performance.now() + 4200; }
function snapshot() { if (lab) state = lab.snapshot(); }
function clearInput() {
  held.clear(); touchHeld.clear(); pointerFire = false; touchFire = false; mousePointer = null; lookPointer = null; dragging = false; aimTarget = null; inputAt = performance.now();
  if (lab) lab.input({ type: 'input', seq: ++seq, moveX: 0, moveZ: 0, yaw, pitch, fire: false, jump: false }, lab.epoch);
}
function syncActive() {
  const visible = playing && !activeDialog && !document.hidden;
  lab?.pause(!visible || !ready || loading || ended);
  world?.setActive(visible && (ready || loading));
  audio.setActive(visible && ready && !loading && !ended);
  inputAt = performance.now();
  snapshot();
}
function applyPreferences() {
  world?.setQuality(preferences.quality); world?.setLightingMode(preferences.lighting); world?.setReducedMotion(preferences.reducedMotion);
  audio.setVolume(.4); audio.setMuted(!preferences.sound);
  $<HTMLSelectElement>('lab-quality').value = preferences.quality; $<HTMLSelectElement>('lab-lighting').value = preferences.lighting;
  $<HTMLInputElement>('lab-reduced-motion').checked = preferences.reducedMotion; $<HTMLInputElement>('lab-sound').checked = preferences.sound;
  $<HTMLInputElement>('lab-sensitivity').value = String(Math.round(preferences.sensitivity * 100)); $('lab-sensitivity-value').textContent = `${preferences.sensitivity.toFixed(1)}×`;
  try { localStorage.setItem('yuga.reference.preferences.v1', JSON.stringify(preferences)); } catch { /* Optional storage. */ }
}
function selectExperiment(id: ReferenceExperiment) {
  if (track === 'lane' && id !== 'lane-economy' || track === 'control' && id !== 'control-point') return;
  experiment = id;
  document.querySelectorAll<HTMLButtonElement>('[data-experiment]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.experiment === id)));
  $('lab-rule-title').textContent = id === 'lane-economy' ? 'Build an advantage. Turn it into a push.' : 'A new objective inside the lane battle.';
  const rules = id === 'lane-economy' ? [
    'Earn credits from the ongoing battle; secure or contest dropped gold before it expires.',
    'Return to base to buy upgrades. Jungle guardians grant temporary powers.',
    'Break two rival towers, then their core. The normal eight-minute arena result applies.',
  ] : [
    `Hold the central ${CONTROL_RULES.radius} m court for ${CONTROL_RULES.captureSeconds} seconds to capture it. Living connected heroes count at height 2 m or lower. More heroes do not speed capture.`,
    'Stay on your owned point to score. A rival contest freezes capture and scoring; an empty point earns nothing.',
    `Lanes, towers and camps remain active. An arena victory wins first; otherwise reach ${CONTROL_RULES.targetScore} hold points, or lead when four minutes expire.`,
  ];
  $('lab-rule-copy').innerHTML = rules.map(rule => `<li>${escape(rule)}</li>`).join('');
  $('lab-launch').textContent = id === 'lane-economy' ? 'Launch lane experiment' : 'Launch hybrid control';
}
function selectHero(id: string) {
  selected = heroById(id); $('lab-hero-name').textContent = selected.name; $('lab-hero-role').textContent = `${selected.role.toUpperCase()} · ${selected.epithet}`;
  $('lab-hero-description').textContent = selected.description;
  $('lab-kit').innerHTML = selected.abilities.map((ability, index) => `<div><kbd>${['Q', 'E', 'R'][index]}</kbd><div><strong>${escape(ability.name)}</strong><span>${escape(ability.description)}</span></div></div>`).join('');
}
function openDialog(id: string) {
  if (loading) return;
  priorFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  activeDialog?.close(); activeDialog = $<HTMLDialogElement>(id); clearInput(); syncActive();
  if (document.pointerLockElement) document.exitPointerLock();
  activeDialog.showModal();
}
function closeDialog() {
  if (!activeDialog) return;
  activeDialog.close(); activeDialog = undefined; clearInput(); syncActive();
  if (playing && !ended) canvas.focus({ preventScroll: true }); else priorFocus?.focus({ preventScroll: true });
}
function settings() {
  $('lab-pause-copy').textContent = playing ? 'This local run is paused. Controls are released while the menu is open.' : 'Preferences apply to both experiments and are saved on this device.';
  $('lab-resume').textContent = playing ? 'Resume run' : 'Done'; $('lab-restart').hidden = !playing; $('lab-back').hidden = !playing;
  openDialog('lab-settings-dialog');
}
function back() {
  generation++; loadAbort?.abort(); clearInput(); playing = false; loading = false; ready = false; ended = false;
  activeDialog?.close(); activeDialog = undefined; lab?.pause(true); world?.setActive(false); audio.setActive(false); state = undefined;
  $('lab-lobby').hidden = false; canvas.hidden = true; $('lab-hud').hidden = true; $('lab-loading').hidden = true;
  $('lab-hud').dataset.ready = 'false';
  $('lab-launch').focus({ preventScroll: true });
}
async function start() {
  if (loading || destroyed) return;
  const seedInput = $<HTMLInputElement>('lab-seed'), seed = Number(seedInput.value);
  if (!seedInput.value || !Number.isSafeInteger(seed) || seed < 0 || seed > 0xffffffff) { $('lab-error').hidden = false; $('lab-error').textContent = 'Choose a whole-number seed from 0 to 4294967295.'; seedInput.focus(); return; }
  activeDialog?.close(); activeDialog = undefined; clearInput(); loadAbort?.abort(); const abort = new AbortController(); loadAbort = abort;
  const request = ++generation; playing = true; loading = true; ready = false; ended = false; warmFrames = 0; renderedFrames = 0; inputSeconds = 0; lastResult = null;
  yaw = 0; pitch = .02; seq = 0; lastEvent = -1; lastReceipt = -1; commandSerial = 0; hitUntil = 0;
  $('lab-receipts').innerHTML = '<li>No wallet changes yet.</li>';
  $('lab-error').hidden = true; $('lab-lobby').hidden = true; canvas.hidden = false; canvas.tabIndex = -1; $('lab-hud').hidden = false; $('lab-hud').inert = true;
  $('lab-hud').dataset.ready = 'false'; $('lab-hud').dataset.warmFrames = '0';
  $('lab-loading').hidden = false; $('lab-loading-copy').textContent = 'Loading Sangam City…'; $('lab-loading-back').focus();
  if (preferences.sound) void audio.unlock().catch(() => { $('lab-audio-status').textContent = 'Audio could not start. Use Preview sound to retry.'; });
  try {
    const options = { experiment, heroId: selected.id, seed };
    if (lab) lab.reset(options); else lab = new ReferenceLab(options);
    lab.pause(true); snapshot();
    if (!world) { creatingWorld ??= createArenaWorld(canvas).catch(error => { creatingWorld = undefined; throw error; }); world = await creatingWorld; }
    if (destroyed) { world.destroy(); return; }
    if (request !== generation) { syncActive(); return; }
    applyPreferences(); world.setOverview(false); world.setCamera(yaw, pitch); world.setActive(!document.hidden);
    const heroIds = [...new Set(state!.arena.actors.filter(actor => actor.kind === 'hero').map(actor => actor.heroId))];
    await world.preloadHeroes(heroIds, (done, total, id) => { if (request === generation) $('lab-loading-copy').textContent = `${heroById(id).name} · ${done} of ${total} participating heroes`; });
    if (request !== generation) return;
    await world.preloadUnits((done, total) => { if (request === generation) $('lab-loading-copy').textContent = `Soldiers & guardians · ${done} of ${total}`; });
    if (request !== generation) return;
    world.resetEventHistory(); world.update(state!.arena, lab.localId, 0); $('lab-loading-copy').textContent = 'Rendering your first view…'; syncActive();
    await waitForRenderedFrames(callback => world!.onRendered(callback), abort.signal, count => { warmFrames = count; $('lab-hud').dataset.warmFrames = String(count); });
    if (request !== generation) return;
    loading = false; ready = true; $('lab-loading').hidden = true; $('lab-hud').inert = false; canvas.tabIndex = 0;
    if (!document.hasFocus()) settings(); else { syncActive(); canvas.focus({ preventScroll: true }); }
    snapshot(); updateHud();
    $('lab-hud').dataset.ready = 'true';
    notify(experiment === 'control-point' ? 'Reach the central court. Capture, then stay to score.' : 'Push with your wave. Earn credits and return to base for upgrades.');
  } catch (error) {
    if (request !== generation || abort.signal.aborted) return;
    back(); $('lab-error').hidden = false; $('lab-error').textContent = error instanceof Error ? error.message : 'The experiment could not load. Retry with Low visual quality.';
  }
}
function action(command: Omit<ReferenceCommand, 'id' | 'type'> | { action: 'ability'; slot: 0 | 1 | 2 } | { action: 'upgrade'; upgrade: 'power' | 'vitality' | 'tempo' }) {
  if (!lab || !playing || !ready || loading || ended || document.hidden || (activeDialog && command.action !== 'upgrade')) return;
  // Immediate abilities receive the current aim without advancing the clock.
  if (!activeDialog) sendInput();
  const result = lab.command({ ...command, type: 'command', id: `lab-${lab.epoch}-${++commandSerial}` } as ReferenceCommand, lab.epoch);
  lastResult = { ok: result.ok, code: result.code }; snapshot(); updateHud();
  const messages: Record<string, string> = { RELOAD_STARTED: 'Reload started.', MAGAZINE_FULL: 'Your primary weapon is already full.', RELOADING: 'Reloading your primary weapon.', CAST_IN_PROGRESS: 'Finish this cast first.', ABILITY_COOLDOWN: 'That ability is still recovering.', RETURN_TO_BASE: 'Return to your own base to buy upgrades.', INSUFFICIENT_CREDITS: 'Earn more credits before buying this rank.', UPGRADE_MAX: 'This upgrade is at its highest rank.', RESPAWNING: 'Wait until your hero returns.', PAUSED: 'Resume the run before taking this action.', STALE_EPOCH: 'The run restarted. Try the action again.' };
  const message = result.ok ? command.action === 'upgrade' ? 'Upgrade purchased. The wallet receipt is recorded.' : command.action === 'reload' ? 'Reload started.' : `${selected.abilities[(command as { slot: number }).slot]?.name ?? 'Ability'} accepted.` : messages[result.code] ?? result.code.toLowerCase().replaceAll('_', ' ');
  if (activeDialog?.id === 'lab-forge-dialog') { $('lab-forge-result').textContent = message; updateForge(); } else { notify(message); canvas.focus({ preventScroll: true }); }
}
function showForge() { if (!active()) return; updateForge(); $('lab-forge-result').textContent = ''; openDialog('lab-forge-dialog'); }
function updateForge() {
  const actor = me(); if (!actor) return;
  $('lab-forge-balance').textContent = `${Math.floor(actor.credits)} credits · ${distance(actor, SPAWNS[actor.team]) <= ARENA_RULES.baseRadius ? 'At your base' : 'Return to your base to purchase'}`;
  document.querySelectorAll<HTMLButtonElement>('[data-upgrade]').forEach(button => {
    const kind = button.dataset.upgrade as keyof typeof UPGRADE_COSTS, rank = actor.upgrades[kind], cost = UPGRADE_COSTS[kind] * (rank + 1);
    button.querySelector('b')!.textContent = rank >= MAX_UPGRADE ? 'MAX' : `${cost} credits · ${rank}/${MAX_UPGRADE}`;
    button.disabled = rank >= MAX_UPGRADE || actor.health <= 0;
  });
}
function finish() {
  if (ended || !state) return; ended = true; clearInput();
  $('lab-result-title').textContent = state.winner === 'draw' ? 'The run ends in a draw.' : state.winner === me()?.team ? 'Your team wins.' : 'The rival team wins.';
  $('lab-result-reason').textContent = state.reason;
  const wallet = state.economy.wallets[state.localId];
  $('lab-result-summary').textContent = `${REFERENCE_EXPERIMENTS.find(item => item.id === state!.experiment)!.title} · Earned ${wallet?.earned ?? 0} · Spent ${wallet?.spent ?? 0}`;
  $('lab-results').innerHTML = state.arena.actors.filter(actor => actor.kind === 'hero').map(actor => `<tr class="${actor.id === state!.localId ? 'you' : ''}"><td>${escape(heroById(actor.heroId).name)}${actor.id === state!.localId ? ' · You' : ' · AI'}</td><td>${actor.kills} / ${actor.assists} / ${actor.deaths}</td><td>${Math.floor(actor.credits)}</td></tr>`).join('');
  openDialog('lab-result-dialog');
}
function updateHud() {
  if (!state) return; const actor = me(); if (!actor) return;
  const point = state.objective, scores = point?.scores ?? state.arena.scores, seconds = Math.max(0, Math.ceil(state.timeLeft));
  $('lab-mode').textContent = state.experiment === 'control-point' ? 'HYBRID CONTROL · LOCAL BOTS' : 'LANE ECONOMY · LOCAL BOTS';
  $('lab-clock').textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  $('lab-score-sun').textContent = String(Math.floor(scores[actor.team])); $('lab-score-moon').textContent = String(Math.floor(scores[actor.team === 'sun' ? 'moon' : 'sun']));
  $('lab-objective').textContent = point ? `Hold to ${point.targetScore} points · Arena victory also counts` : 'Break two rival towers, then their core';
  $('lab-point').hidden = !point;
  if (point) {
    $('lab-point-owner').textContent = point.owner ? `${point.owner === actor.team ? 'Your team' : 'Rivals'} own the court` : 'Unclaimed court';
    $('lab-point-occupants').textContent = `Sun ${point.occupants.sun} · Moon ${point.occupants.moon} heroes in the court`;
    $('lab-point-progress').style.width = `${Math.round(point.progress * 100)}%`;
    $('lab-point-progress').setAttribute('aria-label', `Capture ${Math.round(point.progress * 100)} percent`);
    const status = objectiveStatus(point, actor.team);
    $('lab-point-contested').textContent = status.text; $('lab-point').dataset.state = status.state;
  }
  $('lab-vitals-name').textContent = `${heroById(actor.heroId).name} · ${actor.team.toUpperCase()}`;
  $('lab-health').textContent = `${Math.ceil(actor.health)} / ${actor.maxHealth}${actor.shield > 0 ? ` · ${Math.ceil(actor.shield)} shield` : ''}`;
  $('lab-health-fill').style.width = `${clamp(actor.health / actor.maxHealth * 100, 0, 100)}%`;
  $('lab-record').textContent = `${actor.kills} defeats · ${actor.assists} assists · ${actor.deaths} falls`;
  $('lab-credits').textContent = String(Math.floor(actor.credits));
  const weapon = state.weapons[actor.id];
  $('lab-ammo').textContent = weapon ? `${weapon.ammo} / ${weapon.capacity}` : '—';
  $('lab-reload-status').textContent = weapon?.reloadRemaining ? `Reloading ${weapon.reloadRemaining.toFixed(1)}s` : weapon?.ammo === 0 ? 'EMPTY · PRESS X' : 'PRIMARY WEAPON';
  $<HTMLButtonElement>('lab-reload').disabled = !weapon || weapon.ammo === weapon.capacity || weapon.reloadRemaining > 0 || actor.health <= 0 || !!actor.cast;
  document.querySelectorAll<HTMLButtonElement>('[data-ability]').forEach(button => {
    const slot = Number(button.dataset.ability), ability = heroById(actor.heroId).abilities[slot]!, remaining = actor.cooldowns[slot] ?? 0;
    button.querySelector('strong')!.textContent = ability.name;
    button.querySelector('span')!.textContent = actor.cast?.slot === slot ? 'CASTING' : remaining > 0 ? `${remaining.toFixed(1)}s` : 'Ready';
    button.disabled = remaining > 0 || actor.health <= 0 || !!actor.cast; button.title = ability.description;
  });
  $('lab-respawn').hidden = actor.health > 0; $('lab-respawn').textContent = `Returning in ${Math.ceil(actor.respawn)}s`;
  const wallet = state.economy.wallets[actor.id]; $('lab-economy-total').textContent = `Earned ${wallet?.earned ?? 0} · Spent ${wallet?.spent ?? 0}`;
  const receipts = state.economy.receipts.filter(receipt => receipt.actorId === actor.id), latest = receipts.at(-1)?.id ?? -1;
  if (latest !== lastReceipt) { lastReceipt = latest; $('lab-receipts').innerHTML = receipts.slice(-3).reverse().map(receipt => `<li>${receipt.kind === 'income' ? '+' : '−'}${Math.abs(receipt.amount)} ${receipt.kind === 'income' ? 'income' : 'purchase'} · ${receipt.balance} balance</li>`).join('') || '<li>No wallet changes yet.</li>'; }
  if (lastEvent >= 0 && state.arena.events.some(event => event.id > lastEvent && event.type === 'hit' && event.actorId === actor.id)) hitUntil = performance.now() + 200;
  lastEvent = state.arena.events.at(-1)?.id ?? -1; drawMap(); audio.update(state.arena, state.localId);
}
function drawMap() {
  if (!state) return; const map = $<HTMLCanvasElement>('lab-map'), ctx = map.getContext('2d'); if (!ctx) return;
  const scale = 1.7, x = (value: number) => map.width / 2 - value * scale, z = (value: number) => map.height / 2 - value * scale;
  ctx.clearRect(0, 0, map.width, map.height); ctx.fillStyle = '#071c24'; ctx.fillRect(0, 0, map.width, map.height);
  ctx.strokeStyle = '#3f5e5c'; ctx.lineWidth = 5;
  for (const lane of [-40, 0, 40]) { ctx.beginPath(); ctx.moveTo(x(0), z(-66)); ctx.lineTo(x(lane), z(-48)); ctx.lineTo(x(lane), z(48)); ctx.lineTo(x(0), z(66)); ctx.stroke(); }
  ctx.fillStyle = '#2a4546'; for (const solid of SOLIDS) ctx.fillRect(x(solid.x + solid.w / 2), z(solid.z + solid.d / 2), solid.w * scale, solid.d * scale);
  const point = state.objective;
  if (point) { ctx.strokeStyle = point.contested ? '#fff1d1' : point.owner === 'moon' ? '#8cdeee' : '#f0ca80'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(x(point.x), z(point.z), point.radius * scale, 0, Math.PI * 2); ctx.stroke(); }
  for (const structure of state.arena.structures) if (structure.health > 0) { ctx.fillStyle = structure.team === 'sun' ? '#d6ac67' : '#78c8db'; ctx.fillRect(x(structure.x) - 4, z(structure.z) - 4, 8, 8); }
  for (const actor of state.arena.actors) if (actor.health > 0) {
    const local = actor.id === state.localId, radius = local ? 5 : actor.kind === 'hero' ? 3.5 : 1.7;
    ctx.fillStyle = local ? '#fff4cf' : actor.team === 'sun' ? '#e8bd6f' : '#8bdbea'; ctx.beginPath();
    if (actor.team === 'moon') { ctx.moveTo(x(actor.x), z(actor.z) - radius); ctx.lineTo(x(actor.x) + radius, z(actor.z)); ctx.lineTo(x(actor.x), z(actor.z) + radius); ctx.lineTo(x(actor.x) - radius, z(actor.z)); ctx.closePath(); }
    else ctx.arc(x(actor.x), z(actor.z), radius, 0, Math.PI * 2); ctx.fill();
  }
  const actor = me(); if (actor) { ctx.strokeStyle = '#fff4ce'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x(actor.x), z(actor.z)); ctx.lineTo(x(actor.x) - Math.sin(yaw) * 15, z(actor.z) - Math.cos(yaw) * 15); ctx.stroke(); }
}
function aim(dx: number, dy: number) { if (dx || dy) aimTarget = null; yaw -= dx * .0025 * preferences.sensitivity; pitch = clamp(pitch - dy * .0025 * preferences.sensitivity, -.75, .75); }
function toggleTarget() {
  if (!active() || !state) return;
  if (aimTarget) { aimTarget = null; notify('Target lock released.'); }
  else { aimTarget = acquireTarget(state.arena, state.localId, yaw, pitch); notify(aimTarget ? 'Target locked. Cover still blocks shots.' : 'Aim near a visible rival within 32 m, then press T.'); }
}
function sendInput() {
  if (!lab || !active()) return;
  let side = Number(pressed('KeyD') || pressed('ArrowRight')) - Number(pressed('KeyA') || pressed('ArrowLeft'));
  let forward = Number(pressed('KeyW') || pressed('ArrowUp')) - Number(pressed('KeyS') || pressed('ArrowDown'));
  const length = Math.hypot(side, forward); if (length > 1) { side /= length; forward /= length; }
  const input: ArenaInput = { type: 'input', seq: ++seq, moveX: -Math.cos(yaw) * side + Math.sin(yaw) * forward, moveZ: Math.sin(yaw) * side + Math.cos(yaw) * forward, yaw, pitch, fire: pointerFire || touchFire || pressed('KeyF'), jump: pressed('Space') };
  lab.input(input, lab.epoch);
}
function drawPoint() {
  const point = state?.objective, actor = me();
  const ring = pointRing, beacon = $('lab-point-beacon');
  if (!point || !world || !actor || ended) { ring.setAttribute('hidden', ''); beacon.hidden = true; return; }
  const separation = distance(actor, point), center = world.project({ x: point.x, y: 2, z: point.z });
  beacon.hidden = !center.visible || separation < 12;
  if (center.visible) { beacon.style.left = `${center.x}px`; beacon.style.top = `${center.y}px`; beacon.querySelector('span')!.textContent = `${Math.round(separation)} m · ${point.contested ? 'Contested' : point.owner ? `${point.owner} control` : 'Unclaimed'}`; }
  ring.toggleAttribute('hidden', separation > 28); if (separation > 28) return;
  ring.dataset.owner = point.owner ?? 'none'; ring.dataset.contested = String(point.contested);
  for (let i = 0; i < pointLines.length; i++) {
    const a = i / pointLines.length * Math.PI * 2, b = (i + .72) / pointLines.length * Math.PI * 2;
    const p = world.project({ x: point.x + Math.sin(a) * point.radius, y: .085, z: point.z + Math.cos(a) * point.radius });
    const q = world.project({ x: point.x + Math.sin(b) * point.radius, y: .085, z: point.z + Math.cos(b) * point.radius });
    const line = pointLines[i]!; line.style.display = p.visible && q.visible ? '' : 'none';
    if (p.visible && q.visible) { line.setAttribute('x1', String(p.x)); line.setAttribute('y1', String(p.y)); line.setAttribute('x2', String(q.x)); line.setAttribute('y2', String(q.y)); }
  }
}

document.querySelectorAll<HTMLButtonElement>('[data-experiment]').forEach(button => {
  button.hidden = track === 'lane' && button.dataset.experiment !== 'lane-economy' || track === 'control' && button.dataset.experiment !== 'control-point';
  button.onclick = () => selectExperiment(button.dataset.experiment as ReferenceExperiment);
});
$<HTMLSelectElement>('lab-hero').onchange = event => selectHero((event.target as HTMLSelectElement).value);
$('lab-launch').onclick = () => void start(); $('lab-loading-back').onclick = back; $('lab-lobby-settings').onclick = settings; $('lab-pause').onclick = settings;
$('lab-help').onclick = () => { if (active()) openDialog('lab-controls-dialog'); };
$('lab-resume').onclick = closeDialog; $('lab-back').onclick = back; $('lab-result-back').onclick = back;
$('lab-restart').onclick = () => void start(); $('lab-result-restart').onclick = () => void start();
document.querySelectorAll<HTMLButtonElement>('[data-close]').forEach(button => button.onclick = closeDialog);
document.querySelectorAll<HTMLDialogElement>('dialog').forEach(dialog => dialog.addEventListener('cancel', event => { event.preventDefault(); if (dialog.id === 'lab-result-dialog') back(); else closeDialog(); }));
$<HTMLSelectElement>('lab-quality').onchange = event => { preferences.quality = (event.target as HTMLSelectElement).value as Preferences['quality']; applyPreferences(); };
$<HTMLSelectElement>('lab-lighting').onchange = event => { preferences.lighting = (event.target as HTMLSelectElement).value as Preferences['lighting']; applyPreferences(); };
$<HTMLInputElement>('lab-sensitivity').oninput = event => { preferences.sensitivity = Number((event.target as HTMLInputElement).value) / 100; applyPreferences(); };
$<HTMLInputElement>('lab-reduced-motion').onchange = event => { preferences.reducedMotion = (event.target as HTMLInputElement).checked; applyPreferences(); };
$<HTMLInputElement>('lab-sound').onchange = event => { preferences.sound = (event.target as HTMLInputElement).checked; applyPreferences(); if (preferences.sound) void audio.unlock().catch(() => { $('lab-audio-status').textContent = 'Audio could not start. Try Preview sound.'; }); };
$('lab-sound-preview').onclick = () => { void audio.preview().then(() => { $('lab-audio-status').textContent = 'Preview played. Your audio preference is unchanged.'; }).catch(() => { $('lab-audio-status').textContent = 'Audio is unavailable in this browser.'; }); };
document.querySelectorAll<HTMLButtonElement>('[data-ability]').forEach(button => button.onclick = () => action({ action: 'ability', slot: Number(button.dataset.ability) as 0 | 1 | 2 }));
$('lab-reload').onclick = () => action({ action: 'reload' }); $('lab-forge').onclick = showForge;
document.querySelectorAll<HTMLButtonElement>('[data-upgrade]').forEach(button => button.onclick = () => action({ action: 'upgrade', upgrade: button.dataset.upgrade as 'power' | 'vitality' | 'tempo' }));
$('lab-touch-target').onclick = toggleTarget;
const gameplayKeys = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'KeyI', 'KeyJ', 'KeyK', 'KeyL', 'KeyF', 'Space', 'KeyQ', 'KeyE', 'KeyR', 'KeyX', 'KeyT', 'KeyB']);
window.addEventListener('keydown', event => {
  if (event.code === 'Escape' && active()) { event.preventDefault(); settings(); return; }
  if (!active() || (event.target instanceof HTMLElement && event.target.closest('input,select,textarea'))) return;
  if ((event.code === 'Space' || event.code === 'Enter') && event.target instanceof HTMLElement && event.target.closest('button,a,summary')) return;
  if (!gameplayKeys.has(event.code)) return; event.preventDefault(); held.add(event.code);
  if (event.repeat) return;
  const slot = ['KeyQ', 'KeyE', 'KeyR'].indexOf(event.code);
  if (slot >= 0) action({ action: 'ability', slot: slot as 0 | 1 | 2 });
  else if (event.code === 'KeyX') action({ action: 'reload' }); else if (event.code === 'KeyT') toggleTarget(); else if (event.code === 'KeyB') showForge();
});
window.addEventListener('keyup', event => held.delete(event.code));
window.addEventListener('blur', () => { clearInput(); if (active()) settings(); });
document.addEventListener('visibilitychange', () => { clearInput(); if (document.hidden && playing && ready && !loading && !activeDialog && !ended) settings(); syncActive(); });
canvas.addEventListener('contextmenu', event => event.preventDefault());
canvas.addEventListener('pointerdown', event => {
  if (!active()) return; canvas.focus();
  if (event.pointerType === 'mouse') { mousePointer = event.pointerId; canvas.setPointerCapture(event.pointerId); }
  else { event.preventDefault(); lookPointer = event.pointerId; lastX = event.clientX; lastY = event.clientY; canvas.setPointerCapture(event.pointerId); }
});
canvas.addEventListener('mousedown', event => {
  if (!active() || mousePointer === null) return;
  if (event.button === 2) { toggleTarget(); return; }
  if (event.button !== 0) return; pointerFire = true; dragging = true; lastX = event.clientX; lastY = event.clientY;
});
window.addEventListener('pointermove', event => {
  if (!active()) return;
  if (event.pointerId === lookPointer || dragging && event.pointerType === 'mouse') { aim(event.clientX - lastX, event.clientY - lastY); lastX = event.clientX; lastY = event.clientY; }
});
window.addEventListener('mouseup', event => { if (event.button === 0) { pointerFire = false; dragging = false; } });
const releasePointer = (event: PointerEvent) => { if (event.pointerId === mousePointer) { pointerFire = false; dragging = false; mousePointer = null; } if (event.pointerId === lookPointer) lookPointer = null; };
window.addEventListener('pointerup', releasePointer); canvas.addEventListener('pointercancel', releasePointer); canvas.addEventListener('lostpointercapture', releasePointer);
function heldTouch(element: HTMLElement, begin: () => void, end: () => void) {
  let pointer: number | null = null;
  element.addEventListener('pointerdown', event => { if (!active()) return; event.preventDefault(); pointer = event.pointerId; element.setPointerCapture(event.pointerId); begin(); });
  const release = (event: PointerEvent) => { if (pointer === event.pointerId) { pointer = null; end(); } };
  for (const name of ['pointerup', 'pointercancel', 'lostpointercapture'] as const) element.addEventListener(name, release);
}
document.querySelectorAll<HTMLElement>('[data-touch-key]').forEach(element => heldTouch(element, () => touchHeld.add(element.dataset.touchKey!), () => touchHeld.delete(element.dataset.touchKey!)));
heldTouch($('lab-touch-fire'), () => { touchFire = true; }, () => { touchFire = false; });

const timer = window.setInterval(() => {
  const now = performance.now(), dt = clamp((now - inputAt) / 1000, 0, REFERENCE_RULES.maxElapsed); inputAt = now;
  if (!active() || !lab) return;
  const turn = Number(pressed('KeyL')) - Number(pressed('KeyJ')), tilt = Number(pressed('KeyI')) - Number(pressed('KeyK'));
  if (turn || tilt) { aimTarget = null; yaw -= turn * dt * 1.8 * preferences.sensitivity; pitch = clamp(pitch + tilt * dt * 1.3 * preferences.sensitivity, -.75, .75); inputSeconds += dt; }
  if (aimTarget && state) { const target = targetAim(state.arena, state.localId, aimTarget); if (target) { yaw = target.yaw; pitch = target.pitch; } else aimTarget = null; }
  sendInput(); lab.step(dt); snapshot(); updateHud(); if (state?.phase === 'finished') finish();
}, 50);
function frame(now: number) {
  if (destroyed) return;
  const dt = clamp((now - frameAt) / 1000, 0, .1); frameAt = now;
  if (playing && world && state && !activeDialog && !document.hidden) {
    world.setCamera(yaw, pitch); world.update(state.arena, state.localId, dt); renderedFrames++;
    const reticle = world.reticle(); $('lab-reticle').hidden = !reticle?.visible || loading || ended;
    if (reticle) { $('lab-reticle').style.left = `${reticle.x}px`; $('lab-reticle').style.top = `${reticle.y}px`; }
    $('lab-reticle').classList.toggle('hit', now < hitUntil); drawPoint();
    const target = aimTarget ? targetAim(state.arena, state.localId, aimTarget) : null, projected = target ? world.project(target) : null;
    $('lab-target').hidden = !projected?.visible;
    if (target && projected?.visible) { $('lab-target').textContent = `${target.label} · LOCKED`; $('lab-target').style.left = `${projected.x}px`; $('lab-target').style.top = `${projected.y - 24}px`; }
    if (now > toastUntil) $('lab-toast').hidden = true;
    if (now - lastHud > 200) { lastHud = now; updateHud(); }
  }
  requestAnimationFrame(frame);
}
selectExperiment(experiment); selectHero(selected.id); applyPreferences(); requestAnimationFrame(frame);
if (import.meta.env.DEV) Object.defineProperty(window, '__YUGA_LAB', { value: Object.freeze({
  snapshot: () => state ? structuredClone(state) : undefined,
  playerId: () => state?.localId ?? '',
  metrics: () => ({ ready, loading, playing, ended, paused: !!activeDialog || document.hidden, yaw, pitch, warmFrames, renderedFrames, inputSeconds, lastResult: lastResult ? { ...lastResult } : null }),
  assets: () => world?.assetDiagnostics(),
}), writable: false });
window.addEventListener('pagehide', event => {
  back(); if (event.persisted) return;
  destroyed = true; window.clearInterval(timer); loadAbort?.abort(); lab?.dispose(); audio.destroy(); world?.destroy();
});
