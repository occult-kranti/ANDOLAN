import './style.css';
import { createWorld } from './world/index';
import { connectSolo, connectOnline, getServerUrl, validateServerUrl, hasSave, type Connection } from './connection';
import { GameAudio } from './audio';
import { CityJobs, secondsLeft } from './city-jobs';
import { DEFAULT_BINDINGS, actionHeld, bindingProblem, driveThrottle, keyLabel, restoreBindings, type Binding } from './controls';
import { Simulation } from '../../../packages/sim/src/index';
import { WORLD, landmark } from '../../../packages/sim/src/world';
import { CAMPAIGN, EVIDENCE, getChoiceConsequence, getDocumentStatus } from '../../../packages/content/src/index';
import { CONTRACTS, CITY_EXPOSE_JOB_ID, CITY_SECTORS, PROJECT_MILESTONES, getProjectLevel } from '../../../packages/content/src/contracts';
import type { Snapshot, PlayerSnapshot, InputMessage, CommandAction, Gameplay } from '../../../packages/protocol/src/index';

const $ = <T extends HTMLElement = HTMLElement>(selector: string) => document.querySelector<T>(selector)!;
const app = $('#app');
app.innerHTML = `
  <div class="title-screen" id="title">
    <header class="masthead"><div class="masthead-name"><span class="brandmark">A</span> A city built together</div><span class="build-tag">CITY REFORM · MULTIPLAYER BETA 0.3</span></header>
    <section class="title-body">
      <p class="eyebrow title-location">Devnagar / your next shift starts here</p>
      <h1 class="display">ANDOLAN</h1><h2 class="display">The city is our business.</h2>
      <p class="title-description">Find your crew. Pick a job. Take the wheel.<br>Expose a broadcast. Fix the city. Decide who gets the power.</p>
      <nav class="play-menu" aria-label="Play modes">
        <button class="button primary play-main" id="play-private"><span>Bring your crew<small>Online · create or join a private room</small></span><span class="arrow"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 18 18 6M6 6h12v12"/></svg></span></button>
        <div class="secondary-actions"><button class="button" id="play-online">Open city <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 18 18 6M6 6h12v12"/></svg></button><button class="button" id="play-practice">City practice <span class="mode-note">SOLO</span></button></div>
        <p id="server-availability" class="server-availability"></p>
        <button class="story-option" id="play-story"><span id="story-label">Begin story</span><small>The original six-chapter solo campaign</small><span aria-hidden="true">→</span></button>
      </nav>
    </section>
    <div class="scene-credit"><span class="line"></span><p>OLD MARKET / AFTER HOURS<br><span>Ten jobs. A city at a crossroads.</span></p></div>
    <footer class="title-foot"><p><strong>Drive with purpose. Leave the city better.</strong><br>Original world · cooperative jobs · shared progress</p><div class="title-controls"><button class="small-link settings-open">Settings & sound</button><button class="small-link" id="about-open">About this beta</button></div></footer>
  </div>
  <main class="hud hidden" id="hud" aria-label="Game controls">
    <div class="hud-top"><section class="mission" aria-label="Current objective"><p class="eyebrow" id="chapter-label">Chapter 01 / 06</p><h2 id="mission-title">Last Delivery</h2><p id="objective">Meet Yusuf at the garage.</p><span class="mission-distance" id="mission-distance"></span><div class="chapter-count" id="chapter-count"></div><button id="vote-status" class="vote-status hidden"></button></section>
    <div class="room-bar"><div class="room-status"><i class="status-dot" id="status-dot"></i><span id="status-text">Story</span></div><button id="reconnect" class="button recovery hidden">Reconnect</button><div class="room-tools"><button class="icon-button hidden" id="jobs-open" aria-label="Open city jobs" title="City jobs (J)">Jobs</button><button class="icon-button" id="journal-open" aria-label="Open evidence journal" title="Evidence journal (J)">▤</button><button class="icon-button" id="crew-open" aria-label="Room and crew" title="Room and crew">♧</button><button class="icon-button" id="sound-quick" aria-label="Enable city sound" title="Enable sound">Sound</button><button class="icon-button settings-open" aria-label="Open settings" title="Settings (Escape)">⚙</button></div><p class="crew" id="crew-count"></p><div id="crew-progress" class="crew-progress hidden"></div></div></div>
    <div class="hud-bottom"><div class="map-wrap"><canvas id="minimap" width="308" height="308" aria-label="District map with your position and objective"></canvas><div class="map-caption"><span>Old Market</span><span>N ↑</span></div></div><div class="street"><h3 id="street-name">Yusuf’s Garage</h3><p id="street-subtitle">DEVNAGAR / MONSOON EVENING</p></div></div>
    <button class="interaction hidden" id="interact"><span class="key" data-binding-label="interact">E</span><span id="interact-text">Talk to Yusuf</span></button>
    <div class="driving hidden" id="driving"><div class="speed" id="speed">0</div><span>KM/H · <span id="seat-name">DRIVER</span></span></div>
    <div class="control-strip"><span><span class="key" id="movement-keys">W A S D</span> Move</span><span><span class="key" data-binding-label="vehicle">F</span> Vehicle</span><span><span class="key">Space</span> Brake</span><span><span class="key">C</span> Recenter</span><span><span class="key">Esc</span> Menu</span></div>
    <div class="subtitle hidden" id="subtitle" aria-live="polite"><strong id="subtitle-speaker"></strong><p id="subtitle-line"></p></div>
    <div class="touch-controls" aria-label="Touch movement"><button class="up" data-key="KeyW" data-touch-action="forward" aria-label="Move forward">↑</button><button class="left" data-key="KeyA" data-touch-action="left" aria-label="Move left">←</button><button class="down" data-key="KeyS" data-touch-action="back" aria-label="Move backward">↓</button><button class="right" data-key="KeyD" data-touch-action="right" aria-label="Move right">→</button></div><div class="touch-actions" aria-label="Vehicle and camera controls"><button id="touch-vehicle" aria-label="Enter or exit vehicle">Vehicle</button><button data-touch-action="brake" aria-label="Hold to brake">Brake</button><button id="touch-camera" aria-label="Recenter camera">Camera</button></div>
  </main>
  <div id="toast" class="toast hidden" role="status"></div>
  <div id="loading" class="loading"><h2>ANDOLAN</h2><div class="loading-track"></div><p id="loading-text">Building the streets of Devnagar…</p></div>
  <dialog id="settings-dialog" aria-labelledby="settings-heading"><header class="dialog-header"><div><p class="eyebrow">Make yourself at home</p><h2 id="settings-heading">Settings & controls</h2></div><button class="close" data-close aria-label="Close settings">×</button></header><div class="dialog-body">
    <div class="setting"><label for="quality">Graphics<small>Low reduces shadows, detail and rendering resolution.</small></label><select id="quality"><option value="high">High</option><option value="low">Low</option></select></div>
    <div class="setting"><label for="comfort">Comfort camera<small>Gentler camera response; no dramatic camera motion.</small></label><input id="comfort" type="checkbox"></div>
    <div class="setting"><label for="captions">Subtitles<small>Full conversations also remain in mission interactions.</small></label><input id="captions" type="checkbox" checked></div>
    <div class="setting"><label for="large-text">Larger dialog text</label><input id="large-text" type="checkbox"></div>
    <div class="setting"><label for="sound">City sound<small>Engines, footsteps, rain and job signals. Starts when you enable it.</small></label><button id="sound" class="button quiet" aria-pressed="false">Enable sound</button></div>
    <div class="setting"><label for="volume">Master volume <output id="volume-value" for="volume">65%</output></label><input id="volume" type="range" min="0" max="100" value="65" aria-valuetext="65 percent"></div><div class="sound-preview-row"><p id="sound-status" role="status">Sound is off.</p><button class="button quiet" id="sound-preview">Test sound</button></div>
    <div class="setting"><label for="music">After-hours radio<small>Original instrumental synth bed. No recorded music.</small></label><input id="music" type="checkbox"></div>
    <div class="setting"><label for="assist">Driving assistance<small>Gentler acceleration with full braking strength.</small></label><input id="assist" type="checkbox"></div>
    <div class="controls-table"><div><span class="key">WASD / ↑↓←→</span> Move / drive</div><div><span class="key">Shift</span> Sprint</div><div><span class="key" data-binding-label="interact">E</span> Interact</div><div><span class="key" data-binding-label="vehicle">F</span> Enter / exit car</div><div><span class="key">Drag / C</span> Look / recenter</div><div><span class="key">J</span> Evidence / city jobs</div><div><span class="key">H</span> Vehicle horn</div><div><span class="key">Space</span> Hold to brake</div></div>
    <p class="muted" style="font-size:11px;margin-top:17px">Gamepad: left stick to move or steer, right stick to look, A to interact, Y to enter or exit, B to brake. Online rooms continue while this menu is open; your input stops.</p>
    <details style="margin-top:17px"><summary>Rebind keyboard controls</summary><div id="bindings"></div><p id="binding-status" role="status" class="binding-status">Choose a control, then press a letter or number. Escape cancels.</p><button class="button quiet" id="bindings-reset">Restore default keys</button></details>
  </div><footer class="dialog-footer"><button class="button quiet" id="return-title">Return to title</button><button class="button primary" data-close>Continue</button></footer></dialog>
  <dialog id="lobby-dialog" aria-labelledby="lobby-heading">
    <header class="dialog-header"><div><p class="eyebrow" id="lobby-eyebrow">Meet on the same streets</p><h2 id="lobby-heading">Private crew</h2></div><button class="close" data-close aria-label="Close lobby">×</button></header>
    <form id="lobby-form"><div class="dialog-body">
      <p class="online-note" id="online-note"></p>
      <div class="form-row"><div class="field"><label for="player-name">Crew name</label><input id="player-name" value="Aadi" maxlength="24" required autocomplete="off"></div><div class="field"><label for="gameplay">What are we playing?</label><select id="gameplay"><option value="freeroam">City jobs · free roam</option><option value="story">Original story · co-op</option></select></div></div>
      <div class="field" id="room-field"><label for="room-input">Room code <span class="muted">(optional)</span></label><input id="room-input" placeholder="Leave blank to create a crew" maxlength="16" pattern="[A-Za-z0-9\\x2d]{3,16}" autocomplete="off"><small>Use the same server, mode and room code as your friends.</small></div>
      <div class="field server-field"><label for="server-input">Game server address</label><input id="server-input" type="url" placeholder="wss://your-game-server/ws" autocomplete="url" spellcheck="false" aria-describedby="server-help" required><small id="server-help">Online play needs a running ANDOLAN server. The public beta website hosts the solo game; enter your crew’s server here.</small></div>
      <p id="lobby-error" class="form-error" role="alert"></p>
      <p class="muted lobby-footnote">Private crews hold up to four players. Shared city progress belongs to the room. No account or payment is needed by the game.</p>
    </div><footer class="dialog-footer"><button class="button quiet" type="button" id="lobby-practice">Try solo practice</button><button class="button primary" type="submit">Join the city <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 18 18 6M6 6h12v12"/></svg></button></footer></form>
  </dialog>
  <dialog id="jobs-dialog" aria-labelledby="jobs-heading"><header class="dialog-header"><div><p class="eyebrow">Devnagar dispatch / crew work</p><h2 id="jobs-heading">Pick your next job.</h2></div><button class="close" data-close aria-label="Close city jobs">×</button></header><div class="jobs-summary" id="jobs-summary"></div><div class="jobs-layout"><nav id="job-list" class="job-list" aria-label="Available city jobs"></nav><section id="job-detail" class="job-detail" aria-label="Job briefing"></section></div><footer class="dialog-footer"><p class="muted" id="jobs-scope"></p><button class="button" data-close>Back to the streets</button></footer></dialog>
  <dialog id="mission-dialog" aria-labelledby="dialog-mission-title"><header class="dialog-header"><div><p class="eyebrow" id="dialog-location">Devnagar</p><h2 id="dialog-mission-title">Last Delivery</h2></div><button class="close" data-close aria-label="Close conversation">×</button></header><div class="dialog-body"><div id="dialogue-lines" class="dialogue-lines"></div><div id="choice-list" class="choice-list"></div><p class="vote-note" id="vote-note"></p></div><footer class="dialog-footer"><button class="button primary" id="dialog-continue">Continue</button></footer></dialog>
  <dialog id="journal-dialog" aria-labelledby="journal-heading"><header class="dialog-header"><div><p class="eyebrow">The newsroom / case notes</p><h2 id="journal-heading">What we know</h2></div><button class="close" data-close aria-label="Close journal">×</button></header><div class="dialog-body"><p class="muted" style="font-size:12px">A discrepancy is a question. Keep the record beside the claim.</p><div id="evidence-list"></div></div><footer class="dialog-footer"><button class="button primary" data-close>Back to the city</button></footer></dialog>
  <dialog id="crew-dialog" aria-labelledby="crew-heading"><header class="dialog-header"><div><p class="eyebrow">Together in Devnagar</p><h2 id="crew-heading">Your crew</h2></div><button class="close" data-close aria-label="Close crew">×</button></header><div class="dialog-body"><p id="crew-description"></p><div id="crew-recap"></div><div id="room-code" class="room-code"></div><div id="crew-list"></div><p class="muted" style="font-size:11px;margin-top:16px">Share your room with friends. Preset signals and nearby horns help you coordinate. Crew credits track completed jobs and belong to this room.</p></div><footer class="dialog-footer"><button class="button" id="signal-ready">Signal: ready</button><button class="button primary" id="copy-invite">Copy invite</button></footer></dialog>
  <dialog id="ending-dialog" aria-labelledby="ending-heading"><header class="dialog-header"><div><p class="eyebrow">First Edition / epilogue</p><h2 id="ending-heading">A city, changed</h2></div><button class="close" data-close aria-label="Return to free roam">×</button></header><div class="dialog-body"><p class="eyebrow">Your story ends with</p><h3 class="ending-title" id="ending-title"></h3><p class="ending-copy" id="ending-copy"></p><div id="ending-history"></div><p class="muted" style="font-size:11px;margin-top:22px">You completed this condensed six-mission preview. The full 22-mission campaign and further districts are in development.</p></div><footer class="dialog-footer"><button class="button" id="replay">Start a new story</button><button class="button primary" data-close>Keep exploring</button></footer></dialog>
  <dialog id="about-dialog" aria-labelledby="about-heading"><header class="dialog-header"><div><p class="eyebrow">City Reform / beta 0.3</p><h2 id="about-heading">A city built together</h2></div><button class="close" data-close aria-label="Close about">×</button></header><div class="dialog-body"><p>ANDOLAN is an original cooperative city game. Drive through Old Market, take repeatable jobs, coordinate deliveries and help a fictional district rebuild.</p><p>City Reform includes five repeatable crew jobs and five linked investigations: the Republic Times exposé, energy, welfare, resources and contracts. The final crew mandate can protect the reforms or betray allies for higher private rewards. These are authored game outcomes in one district. Bring a crew to a game server, or try the same jobs in solo practice. The original six-chapter campaign remains a separate option with its own save.</p><p class="muted">Characters, institutions and events are invented satire. Republic Times and its anchor Grnab Aoswami belong to this fictional city; feed cards are authored jokes, not live news. Engine: PlayCanvas. All game art and synthesized audio are original. REA and pinned open-source references informed controller and multiplayer research; no commercial game code or assets are included.</p><p class="muted">Desktop Chromium with WebGL2 is the primary test environment. Touch controls are provided. Full mobile performance and public service capacity are still to be validated.</p></div><footer class="dialog-footer"><button class="button primary" data-close>Back</button></footer></dialog>
`;

let bindings = { ...DEFAULT_BINDINGS };
let settings = { sound: false, volume: 0.65, music: false, quality: 'high' as 'high' | 'low', comfort: matchMedia('(prefers-reduced-motion: reduce)').matches, captions: true, largeText: false, assist: false };
try { settings = { ...settings, ...JSON.parse(localStorage.getItem('andolan.settings') || '{}') }; bindings = restoreBindings(JSON.parse(localStorage.getItem('andolan.bindings') || '{}')); } catch { /* Defaults remain usable. */ }
let view: Awaited<ReturnType<typeof createWorld>>;
let connection: Connection | undefined;
let snapshot: Snapshot;
let playerId = 'preview';
let playing = false, local = true, connected = false, lobbyMode: 'private' | 'public' = 'private';
let sequence = Date.now(), commandSequence = 0, toastTimer = 0, lastStage = '', endingShown = false;
let lastHistoryLength = -1;
let subtitleStageQueued = '';
let hasWelcomed = false, recapOnSnapshot = false;
let currentServer = getServerUrl();
let lastContractRevision = -1, lastContractId = '', lastContractStage = '', lastOutcomeId = '';
let lastCityOutcome = '', haveCityBaseline = false;
let audioPosition: { x: number; z: number; time: number } | undefined;
let heardSignals = new Map<string, number>(), haveSignalBaseline = false;
let interactionAction: (() => void) | undefined;
const keys = new Set<string>(), touchActions = new Set<string>();
function releaseControls() { keys.clear(); touchActions.clear(); }
const audio = new GameAudio();
const preview = new Simulation('PREVIEW', 'private'); preview.addPlayer('preview', 'Aadi'); snapshot = preview.snapshot();
let subtitleQueue: { speaker: string; text: string }[] = [], subtitleDeadline = 0;
let bindingCapture: Binding | null = null;
function toast(message: string) { $('#toast').textContent = message; $('#toast').classList.remove('hidden'); clearTimeout(toastTimer); toastTimer = window.setTimeout(() => $('#toast').classList.add('hidden'), 5000); }
function modalOpen() { return !!document.querySelector('dialog[open]'); }
function openDialog(id: string) { releaseControls(); document.querySelectorAll<HTMLDialogElement>('dialog[open]').forEach(d => d.close()); $<HTMLDialogElement>(id).showModal(); }
document.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => button.closest('dialog')?.close()));
function command(action: CommandAction, target?: string, value?: string) { connection?.command({ type: 'command', id: `c${Date.now()}_${++commandSequence}`, action, ...(target ? { target } : {}), ...(value ? { value } : {}) }); }
function currentPlayer(): PlayerSnapshot | undefined { return snapshot.players.find(p => p.id === playerId); }
function distance(a: { x: number; z: number }, b: { x: number; z: number }) { return Math.hypot(a.x - b.x, a.z - b.z); }
function textElement(tag: string, text: string, className = '') { const e = document.createElement(tag); e.textContent = text; e.className = className; return e; }
const cityJobs = new CityJobs({ command, open: () => openDialog('#jobs-dialog'), closeAndFocus: () => { $<HTMLDialogElement>('#jobs-dialog').close(); canvas.focus({ preventScroll: true }); } });
$('#jobs-open').addEventListener('click', () => cityJobs.show());
function isCity() { return snapshot.gameplay === 'freeroam'; }
function updateAudio(p: PlayerSnapshot) {
  const car = snapshot.vehicles.find(v => v.id === p.vehicleId);
  const elapsed = audioPosition ? snapshot.time - audioPosition.time : 0;
  const speed = audioPosition && elapsed > 0 ? Math.min(7, distance(p, audioPosition) / elapsed) : 0;
  audioPosition = { x: p.x, z: p.z, time: snapshot.time };
  audio.update(car?.speed || 0, !!car, { walkSpeed: modalOpen() || !connected ? 0 : speed });
}
function updateCityHUD() {
  const p = currentPlayer(), { active, progression, recent, revision } = snapshot.contracts;
  cityJobs.update(snapshot, playerId, local, connected);
  audio.setActivity(playing && connected && !modalOpen() && !document.hidden);
  $('#jobs-open').classList.remove('hidden'); $('#journal-open').classList.add('hidden');
  $('#vote-status').classList.add('hidden'); $('#crew-progress').classList.remove('hidden');
  const job = CONTRACTS.find(item => item.id === active?.jobId);
  const { city } = snapshot;
  const filedSectors = CITY_SECTORS.filter(sector => city.sectors[sector.id] > 0).length;
  const mandateReady = !city.decision && city.completedJobs.includes(CITY_EXPOSE_JOB_ID) && filedSectors === CITY_SECTORS.length;
  const civicTarget = !active && mandateReady ? landmark('civic') : undefined;
  if (haveCityBaseline && city.outcome && city.outcome.id !== lastCityOutcome) { audio.cue('job-complete'); toast(`City Mandate: ${city.outcome.title}. Your crew’s decision is saved in the City ledger.`); }
  lastCityOutcome = city.outcome?.id || ''; haveCityBaseline = true;
  $('#chapter-label').textContent = active ? `City jobs / step ${active.stageIndex + 1} of ${job?.stages.length || 1}` : 'DEVNAGAR DISPATCH / OPEN SHIFT';
  $('#mission-title').textContent = job?.title || city.outcome?.title || (mandateReady ? 'Who gets the power?' : 'The city needs a crew.');
  $('#objective').textContent = active?.objective || (city.decision ? 'Your mandate is saved. Take more crew jobs or revisit the City ledger.' : mandateReady ? 'Meet on foot at Public Hearing. Review the two permanent routes in the City ledger and decide together.' : city.completedJobs.includes(CITY_EXPOSE_JOB_ID) ? 'The media case is filed. Choose an energy, welfare, resources or contracts case in Jobs.' : 'Open Jobs and start The Nine O’Clock Correction. Noor is nearby at The Newsroom.');
  const progressLabel = PROJECT_MILESTONES[getProjectLevel(progression.project)];
  $('#crew-progress').textContent = `${progression.credits} credits · ${progression.reputation} rep\n${filedSectors}/4 sector cases · ${progression.project} project points`;
  $('#crew-progress').title = progressLabel.title;
  $('#crew-count').textContent = local ? 'Solo practice · no online players' : `${snapshot.players.filter(player => player.connected).length} connected crew · shared progress`;
  if (revision !== lastContractRevision) {
    const outcome = recent[0];
    if (lastContractRevision >= 0) {
      if (active && active.instanceId !== lastContractId) { audio.cue('job-start'); toast(`${job?.title || 'Job'} accepted. Your crew shares the objective.`); }
      else if (active && active.stageId !== lastContractStage) {
        audio.cue('job-progress');
        const receipt = job?.stages[active.stageIndex - 1]?.event;
        if (receipt) toast(`${receipt.title} · receipt added to the City ledger.`);
      }
      if (outcome && outcome.instanceId !== lastOutcomeId) {
        audio.cue(outcome.status === 'completed' ? 'job-complete' : 'error');
        toast(outcome.status === 'completed' ? `Job complete · +${outcome.credits} crew credits · +${outcome.reputation} reputation` : `Job ${outcome.status}. Choose another run when you’re ready.`);
      }
    }
    lastContractRevision = revision; lastContractId = active?.instanceId || ''; lastContractStage = active?.stageId || ''; lastOutcomeId = outcome?.instanceId || '';
    $('#chapter-count').replaceChildren(...(job?.stages || []).map((_, index) => textElement('span', '', index <= (active?.stageIndex || 0) ? 'done' : '')));
  }
  const target = active?.targetPosition || civicTarget;
  const stage = job?.stages[active?.stageIndex || 0];
  const targetRadius = active?.targetVehicleId ? 5.8 : landmark(active?.targetId || 'civic')?.radius || 7;
  view?.setObjectiveTarget(target ? { ...target, radius: targetRadius, kind: !active || active.vehicle === 'none' ? 'walk' : active.action === 'checkpoint' && stage?.maxSpeed === undefined ? 'pass' : 'park' } : null);
  if (!p) return;
  $('#mission-distance').textContent = active && target ? `${Math.round(distance(p, target))} M TO OBJECTIVE${active.deadlineAt === null ? '' : ` · ${secondsLeft(active.deadlineAt - snapshot.time)} LEFT`}` : civicTarget ? `${Math.round(distance(p, civicTarget))} M TO PUBLIC HEARING · CITY MANDATE` : 'J / CITY JOBS · CASES, CREW WORK & CITY LEDGER';
  const nearest = [...WORLD.landmarks].sort((a, b) => distance(p, a) - distance(p, b))[0];
  $('#street-name').textContent = nearest && distance(p, nearest) < 27 ? nearest.name : 'Old Market';
  const car = snapshot.vehicles.find(vehicle => vehicle.id === p.vehicleId);
  $('#driving').classList.toggle('hidden', !car);
  if (car) { $('#speed').textContent = String(Math.round(Math.abs(car.speed) * 3.6)); $('#seat-name').textContent = p.seat === 0 ? 'DRIVER' : 'PASSENGER'; }
  updateAudio(p);
  interactionAction = undefined;
  let prompt = '';
  if (connected) {
    const radius = active?.targetVehicleId ? 5.8 : landmark(active?.targetId || '')?.radius || 7;
    if (active && target && active.action === 'interact' && distance(p, target) <= radius) {
      if (active.vehicle === 'none' && car) { prompt = 'Exit vehicle for the handover'; interactionAction = vehicleAction; }
      else if (active.vehicle !== 'none' && car && (active.vehicle !== 'any' && car.kind !== active.vehicle || active.vehicleId && car.id !== active.vehicleId)) {
        prompt = `Wrong vehicle · exit and bring ${active.vehicle === 'van' ? 'the van' : 'the assigned car'}`; interactionAction = vehicleAction;
      } else if (active.vehicle !== 'none' && car && p.seat !== 0) {
        if (!car.occupants[0] && Math.abs(car.speed) <= 1.5) { prompt = 'Take the wheel'; interactionAction = () => command('take_wheel'); }
        else { prompt = 'Driver handles this step · exit vehicle'; interactionAction = vehicleAction; }
      } else if (active.vehicle !== 'none' && !car) {
        const available = snapshot.vehicles.find(vehicle => (active.vehicle === 'any' || vehicle.kind === active.vehicle) && (!active.vehicleId || vehicle.id === active.vehicleId) && distance(p, vehicle) <= 5.8);
        prompt = available ? `Enter the ${available.kind}` : `Bring ${active.vehicle === 'van' ? 'the van' : 'the assigned vehicle'} here · view job`;
        interactionAction = available ? () => command('enter', available.id) : () => cityJobs.show();
      }
      else {
        const stage = job?.stages[active.stageIndex];
        prompt = stage?.grantCargo ? 'Load the vehicle' : stage?.consumeCargo ? 'Unload the delivery' : active.targetVehicleId ? 'Check recovery vehicle' : active.stageIndex === (job?.stages.length || 0) - 1 ? 'Complete job' : 'Check in';
        interactionAction = () => command('job_interact', active.instanceId, active.stageId);
      }
    } else if (car && p.seat !== 0 && !car.occupants[0] && Math.abs(car.speed) <= 1.5) { prompt = 'Take the wheel'; interactionAction = () => command('take_wheel'); }
    else if (car) { prompt = Math.abs(car.speed) > 1 ? 'Hold Space / Brake to stop' : 'Exit vehicle'; interactionAction = vehicleAction; }
    else if (snapshot.vehicles.some(vehicle => distance(p, vehicle) < 5)) { prompt = 'Enter vehicle'; interactionAction = vehicleAction; }
    else if (!active && civicTarget && distance(p, civicTarget) <= civicTarget.radius) { prompt = 'City Mandate · review the crew decision'; interactionAction = () => cityJobs.showLedger(); }
    else if (!active) { prompt = 'Choose a city job'; interactionAction = () => cityJobs.show(); }
  }
  $('#interact-text').textContent = prompt; $('#interact').classList.toggle('hidden', !prompt);
  drawMap(p, target);
}

function showDialogue() {
  const m = snapshot.mission;
  $('#dialog-mission-title').textContent = m.title;
  $('#dialog-location').textContent = landmark(m.targetId || '')?.name || 'Devnagar';
  const lines = $('#dialogue-lines'); lines.replaceChildren();
  for (const line of m.dialogue) {
    const div = document.createElement('div'); div.className = 'dialogue-line';
    div.append(textElement('strong', line.speaker), textElement('p', line.text)); lines.append(div);
  }
  if (!m.dialogue.length) lines.append(textElement('p', m.objective));
  if (m.documents?.length) {
    lines.append(textElement('h3', m.chapterId === 'two-copies' ? 'Compare the two records' : 'The hearing case bundle', 'display'));
    for (const id of m.documents) {
      const evidence = EVIDENCE[id]; if (!evidence) continue;
      const article = document.createElement('article'); article.className = 'paper';
      article.append(textElement('h3', evidence.title), textElement('p', evidence.body), textElement('p', evidence.qualification), textElement('p', `Source: ${evidence.source}`), textElement('p', getDocumentStatus(id, m.history)));
      lines.append(article);
    }
  }
  const choices = $('#choice-list'); choices.replaceChildren();
  for (const choice of m.choices) {
    const button = document.createElement('button'); button.className = 'choice';
    button.append(textElement('strong', choice.label), textElement('small', choice.description));
    button.dataset.choice = choice.id;
    button.addEventListener('click', () => { command('choice', m.targetId || undefined, choice.id); if (local) $<HTMLDialogElement>('#mission-dialog').close(); else updateVoteFeedback(); }); choices.append(button);
  }
  updateVoteFeedback();
  $('#dialog-continue').classList.toggle('hidden', m.choices.length > 0);
  openDialog('#mission-dialog');
}
function updateVoteFeedback() {
  const m = snapshot.mission;
  if (!m.choices.length || local) { $('#vote-note').textContent = ''; return; }
  const active = snapshot.players.filter(p => p.connected).length;
  const needed = snapshot.mode === 'private' ? Math.floor(active / 2) + 1 : 1;
  for (const button of document.querySelectorAll<HTMLButtonElement>('[data-choice]')) {
    const choice = m.choices.find(c => c.id === button.dataset.choice); if (!choice) continue;
    const count = Object.values(m.votes).filter(v => v === choice.id).length;
    const selected = m.votes[playerId] === choice.id;
    button.querySelector('strong')!.textContent = `${choice.label} · ${count} ${count === 1 ? 'vote' : 'votes'}${selected ? ' · your choice' : ''}`;
    button.setAttribute('aria-pressed', String(selected));
  }
  $('#vote-note').textContent = `${needed} matching ${needed === 1 ? 'vote' : 'votes'} needed from ${active} connected crew. You can change your vote. A tie waits for agreement. If someone leaves, the majority is recalculated from the remaining crew.`;
}
$('#dialog-continue').addEventListener('click', () => { const m = snapshot.mission; $<HTMLDialogElement>('#mission-dialog').close(); command('interact', m.targetId || undefined); });
function interact() {
  if (!playing || modalOpen()) return;
  if (interactionAction) interactionAction(); else toast('Follow the amber destination on your map.');
}
function vehicleAction() {
  if (!playing || modalOpen()) return;
  const p = currentPlayer(); if (!p || !connected) return;
  if (p.vehicleId) command('exit'); else {
    const car = [...snapshot.vehicles].sort((a, b) => distance(p, a) - distance(p, b))[0];
    if (car) command('enter', car.id);
  }
}
function focusPlay() { if (playing && !modalOpen()) canvas.focus({ preventScroll: true }); }
$('#interact').addEventListener('click', () => { interact(); focusPlay(); });

function updateHUD() {
  if (!playing) return;
  if (isCity()) { updateCityHUD(); return; }
  view?.setObjectiveTarget(undefined);
  $('#jobs-open').classList.add('hidden'); $('#journal-open').classList.remove('hidden'); $('#crew-progress').classList.add('hidden');
  const m = snapshot.mission, p = currentPlayer();
  if (lastHistoryLength >= 0 && m.history.length > lastHistoryLength) {
    const last = m.history.at(-1)!;
    toast(getChoiceConsequence(last) || `Recorded: ${last.label}`);
  }
  lastHistoryLength = m.history.length;
  $('#mission-title').textContent = m.title;
  $('#chapter-label').textContent = m.complete ? 'First Edition / completed' : `Chapter ${String(m.chapterIndex + 1).padStart(2, '0')} / ${String(CAMPAIGN.length).padStart(2, '0')}`;
  $('#objective').textContent = m.complete ? 'Your city is still here. Explore, or revisit your story.' : m.objective;
  const stageKey = `${m.chapterIndex}:${m.stageIndex}`;
  if (stageKey !== lastStage) {
    lastStage = stageKey;
    $('#chapter-count').replaceChildren(...CAMPAIGN.map((_, i) => textElement('span', '', i <= m.chapterIndex ? 'done' : '')));
    subtitleQueue = []; subtitleDeadline = 0; subtitleStageQueued = ''; $('#subtitle').classList.add('hidden');
    if ($<HTMLDialogElement>('#mission-dialog').open) $<HTMLDialogElement>('#mission-dialog').close();
  }
  if ($<HTMLDialogElement>('#mission-dialog').open) updateVoteFeedback();
  if (m.complete && m.ending && !endingShown) { endingShown = true; showEnding(); }
  const active = snapshot.players.filter(p => p.connected);
  $('#crew-count').textContent = local ? 'Aadi · Solo story' : `${active.length} ${active.length === 1 ? 'player' : 'players'} in this room`;
  if (!p) return;
  const target = landmark(m.targetId || '');
  if (subtitleStageQueued !== stageKey && !m.complete && (['arrive', 'enter_vehicle'].includes(m.trigger) || (target && distance(p, target) <= target.radius))) {
    subtitleQueue = [...m.dialogue]; subtitleDeadline = 0; subtitleStageQueued = stageKey;
  }
  const ballots = Object.values(m.votes);
  const needed = snapshot.mode === 'private' ? Math.floor(active.length / 2) + 1 : 1;
  const myVote = m.choices.find(c => c.id === m.votes[playerId]);
  const voteHint = !target || distance(p, target) > target.radius
    ? `Travel to ${target?.name || 'the destination'} to vote.`
    : p.vehicleId
      ? 'Stop and exit the vehicle, then interact to vote.'
      : `Press ${bindings.interact.replace('Key', '').replace('Digit', '')} or use Interact to vote.`;
  $('#vote-status').classList.toggle('hidden', local || !ballots.length);
  $('#vote-status').textContent = `Crew decision · ${ballots.length}/${active.length} voted · ${needed} matching needed. ${myVote ? `Your vote: ${myVote.label}.` : voteHint}`;

  $('#mission-distance').textContent = target ? `${target.name.toUpperCase()} · ${Math.round(distance(p, target))} M` : 'FREE ROAM · YOUR RECORDS ARE SAVED';
  const nearest = [...WORLD.landmarks].sort((a, b) => distance(p, a) - distance(p, b))[0];
  $('#street-name').textContent = nearest && distance(p, nearest) < 27 ? nearest.name : 'Old Market';
  const car = snapshot.vehicles.find(v => v.id === p.vehicleId);
  $('#driving').classList.toggle('hidden', !car);
  if (car) { $('#speed').textContent = String(Math.round(Math.abs(car.speed) * 3.6)); $('#seat-name').textContent = p.seat === 0 ? 'DRIVER' : 'PASSENGER'; }
  updateAudio(p);
  interactionAction = undefined;
  let prompt = '';
  if (connected) {
    if (!p.vehicleId && target && distance(p, target) <= target.radius && !m.complete && ['interact', 'choice'].includes(m.trigger)) {
      prompt = m.trigger === 'choice' ? 'Listen & choose' : `Interact · ${target.name}`;
      interactionAction = showDialogue;
    } else if (car && p.seat !== 0 && !car.occupants[0] && Math.abs(car.speed) <= 1.5) { prompt = 'Take the wheel'; interactionAction = () => command('take_wheel'); }
    else if (car) { prompt = Math.abs(car.speed) > 1 ? 'Hold Space / Brake to stop' : 'Exit vehicle'; interactionAction = vehicleAction; }
    else {
      const closestCar = snapshot.vehicles.find(v => distance(p, v) < 5);
      if (closestCar) { prompt = `Enter ${closestCar.kind === 'van' ? 'van' : 'car'}`; interactionAction = vehicleAction; }
      else if (m.complete && nearest?.id === 'board' && distance(p, nearest) < 8) { prompt = 'Read your story'; interactionAction = showEnding; }
    }
  }
  $('#interact-text').textContent = prompt;
  $('#interact').classList.toggle('hidden', !prompt);
  drawMap(p, target);
}
function drawMap(p: PlayerSnapshot, target?: { x: number; z: number }) {
  const c = $<HTMLCanvasElement>('#minimap').getContext('2d')!;
  const size = 308, scale = 1.4, cx = (x: number) => size / 2 + x * scale, cz = (z: number) => size / 2 + z * scale;
  c.fillStyle = '#1c353b'; c.fillRect(0, 0, size, size);
  c.fillStyle = '#3a5255';
  for (const road of WORLD.roads) { c.fillRect(cx(road - 6.5), 0, 13 * scale, size); c.fillRect(0, cz(road - 6.5), size, 13 * scale); }
  c.fillStyle = '#62736b';
  for (const b of WORLD.buildings) c.fillRect(cx(b.x - b.width / 2), cz(b.z - b.depth / 2), b.width * scale, b.depth * scale);
  for (const l of WORLD.landmarks) { c.fillStyle = '#c5c5aa'; c.fillRect(cx(l.x) - 2, cz(l.z) - 2, 4, 4); }
  if (target) {
    c.strokeStyle = '#e8b564'; c.lineWidth = 2; c.setLineDash([4, 5]);
    c.beginPath(); c.moveTo(cx(p.x), cz(p.z)); c.lineTo(cx(target.x), cz(target.z)); c.stroke(); c.setLineDash([]);
    c.fillStyle = '#f5c878'; c.beginPath(); c.arc(cx(target.x), cz(target.z), 7, 0, Math.PI * 2); c.fill();
  }
  for (const car of snapshot.vehicles) {
    c.fillStyle = '#d6ded1'; c.fillRect(cx(car.x) - 8, cz(car.z) - 8, 16, 16);
    c.fillStyle = '#142e32'; c.font = 'bold 13px sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(car.kind === 'van' ? 'V' : 'C', cx(car.x), cz(car.z) + .5);
  }
  for (const other of snapshot.players.filter(a => a.connected && a.id !== p.id)) { c.fillStyle = '#8bd3cb'; c.beginPath(); c.arc(cx(other.x), cz(other.z), 5, 0, Math.PI * 2); c.fill(); }
  c.save(); c.translate(cx(p.x), cz(p.z)); c.rotate(-p.heading); c.fillStyle = '#fff7e5';
  c.beginPath(); c.moveTo(0, 9); c.lineTo(-6, -6); c.lineTo(0, -3); c.lineTo(6, -6); c.closePath(); c.fill(); c.restore();
}
function showJournal() {
  if (isCity()) { cityJobs.show(); return; }
  const list = $('#evidence-list'); list.replaceChildren();
  if (!snapshot.mission.evidence.length) list.append(textElement('p', 'Your board is empty. Complete the first delivery to find the first lead.', 'evidence-empty'));
  for (const id of snapshot.mission.evidence) {
    const evidence = EVIDENCE[id]; if (!evidence) continue;
    const div = document.createElement('article'); div.className = 'paper';
    div.append(textElement('h3', evidence.title), textElement('p', evidence.body), textElement('p', evidence.qualification), textElement('p', `Source: ${evidence.source}`), textElement('p', getDocumentStatus(id, snapshot.mission.history))); list.append(div);
  }
  if (snapshot.mission.history.length) {
    list.append(textElement('h3', 'Choices & consequences', 'display'));
    for (const entry of snapshot.mission.history) {
      const article = document.createElement('article'); article.className = 'paper';
      article.append(textElement('h3', entry.label), textElement('p', getChoiceConsequence(entry)));
      list.append(article);
    }
  }
  openDialog('#journal-dialog');
}
$('#journal-open').addEventListener('click', showJournal);
function showEnding() {
  const ending = snapshot.mission.ending; if (!ending) return;
  $('#ending-title').textContent = ending.title; $('#ending-copy').textContent = ending.description;
  const history = $('#ending-history'); history.replaceChildren();
  for (const choice of snapshot.mission.history.slice(-6)) history.append(textElement('p', `• ${choice.label}`, 'muted'));
  openDialog('#ending-dialog');
}
$('#replay').addEventListener('click', () => {
  if (!window.confirm('Start a new story? This replaces the completed story in this room.')) return;
  endingShown = false; command('replay', undefined, 'confirm'); $<HTMLDialogElement>('#ending-dialog').close();
});
function showCrew() {
  $('#crew-description').textContent = local ? 'This session is solo. Return to the title and bring your crew to share a city on a game server.' : 'Invite a friend using this room code. Join the same server and game mode to share your city.';
  $('#room-code').textContent = local ? (isCity() ? 'SOLO PRACTICE' : 'SOLO STORY') : snapshot.room;
  const list = $('#crew-list'); list.replaceChildren();
  for (const p of snapshot.players) list.append(textElement('p', `${p.name}${p.id === playerId ? ' (you)' : ''} · ${p.connected ? 'here' : 'disconnected'} · ${p.vehicleId ? (p.seat === 0 ? 'driving' : 'passenger') : 'on foot'}${p.signal ? ` · ${p.signal}` : ''}`));
  const recap = $('#crew-recap');
  if (isCity()) {
    const { active, progression, recent } = snapshot.contracts;
    recap.replaceChildren(textElement('h3', active ? CONTRACTS.find(job => job.id === active.jobId)?.title || 'Crew job' : 'Open shift', 'display'), textElement('p', active?.objective || 'Choose a city job. Everyone in this room shares the objective and rewards.'));
    recap.append(textElement('p', `${progression.completed} jobs / ${progression.credits} shared credits / ${progression.reputation} reputation`, 'recap-line'));
    for (const outcome of recent.slice(0, 3)) recap.append(textElement('p', `${CONTRACTS.find(job => job.id === outcome.jobId)?.title || outcome.jobId} · ${outcome.status}${outcome.status === 'completed' ? ` · +${outcome.credits} credits` : ''}`, 'recap-line'));
  } else {
    recap.replaceChildren(textElement('h3', snapshot.mission.title, 'display'), textElement('p', snapshot.mission.objective));
    for (const entry of snapshot.mission.history.slice(-3)) recap.append(textElement('p', getChoiceConsequence(entry), 'recap-line'));
    if (Object.keys(snapshot.mission.votes).length) recap.append(textElement('p', $('#vote-status').textContent || '', 'vote-note'));
  }

  $<HTMLButtonElement>('#copy-invite').disabled = local;
  openDialog('#crew-dialog');
}
$('#crew-open').addEventListener('click', showCrew);
$('#vote-status').addEventListener('click', showCrew);
$('#reconnect').addEventListener('click', () => connection?.reconnect?.());
$('#copy-invite').addEventListener('click', async () => { try { const url = new URL(location.href); url.searchParams.set('room', snapshot.room); url.searchParams.set('mode', snapshot.mode); url.searchParams.set('gameplay', snapshot.gameplay || 'story'); if (currentServer) url.searchParams.set('server', currentServer); await navigator.clipboard.writeText(url.toString()); toast('Invite link copied.'); } catch { toast(`Share room code ${snapshot.room}, game mode ${isCity() ? 'City jobs' : 'Story'}, and your server address.`); } });
$('#signal-ready').addEventListener('click', () => { command('signal', undefined, 'ready'); audio.cue('signal'); toast('Ready signal sent to your room.'); });

const callbacks = {
  snapshot: (state: Snapshot) => {
    snapshot = state;
    const me = currentPlayer();
    if (haveSignalBaseline && me) for (const other of state.players) {
      if (other.id !== playerId && other.signal && other.signalUntil > state.time && other.signalUntil !== heardSignals.get(other.id) && distance(me, other) < 45) audio.cue(other.signal === 'horn' ? 'horn' : 'signal');
    }
    heardSignals = new Map(state.players.map(player => [player.id, player.signalUntil])); haveSignalBaseline = true;
    updateHUD(); if (recapOnSnapshot) { recapOnSnapshot = false; if (state.gameplay === 'freeroam') { if (state.contracts.active || state.contracts.progression.completed) toast('Crew progress restored. Open Jobs for the current task or City ledger.'); } else if (state.mission.history.length > 0 && !state.mission.complete) showCrew(); }
  },
  welcome: (id: string, _room: string, isLocal: boolean) => { playerId = id; local = isLocal; sequence = Date.now(); view.resetInterpolation(); audioPosition = undefined; haveSignalBaseline = false; heardSignals.clear(); recapOnSnapshot = !isLocal && !hasWelcomed; hasWelcomed = true; },
  status: (message: string, online: boolean) => { connected = online; $('#status-text').textContent = message; $('#status-dot').style.background = online ? '#bed7a6' : '#e3a25d'; $('#reconnect').classList.toggle('hidden', online || local); if (isCity()) cityJobs.update(snapshot, playerId, local, connected); },
  error: (message: string) => { cityJobs.clearPending(message); audio.cue('error'); toast(message); },
};
function begin(mode: 'solo' | 'private' | 'public', room?: string, gameplay: Gameplay = 'story') {
  connection?.close(); releaseControls(); lastStage = ''; endingShown = false; lastHistoryLength = -1; hasWelcomed = false; recapOnSnapshot = false; local = mode === 'solo';
  lastContractRevision = -1; lastContractId = ''; lastContractStage = ''; lastOutcomeId = ''; lastCityOutcome = ''; haveCityBaseline = false; audioPosition = undefined;
  document.querySelectorAll<HTMLDialogElement>('dialog[open]').forEach(d => d.close());
  playing = true; connected = false; $('#title').classList.add('hidden'); $('#hud').classList.remove('hidden'); canvas.focus({ preventScroll: true });
  (view as typeof view & { setOverview?: (value: boolean) => void }).setOverview?.(false);
  const name = $<HTMLInputElement>('#player-name').value.trim() || 'Aadi';
  audio.configure({ volume: settings.volume, music: settings.music }); audio.setActivity(true);
  if (settings.sound) void audio.enable().then(updateSoundLabel).catch(() => toast('Audio could not start. Try Enable sound in Settings.'));
  connection = mode === 'solo' ? connectSolo(name, callbacks, false, gameplay) : connectOnline({ type: 'join', mode, gameplay, name, ...(room ? { room } : {}) }, callbacks, currentServer);
}
$('#play-story').addEventListener('click', () => begin('solo'));
$('#play-practice').addEventListener('click', () => begin('solo', undefined, 'freeroam'));
$('#lobby-practice').addEventListener('click', () => begin('solo', undefined, 'freeroam'));
function showLobby(mode: 'private' | 'public', room = '', gameplay: Gameplay = 'freeroam', server = currentServer) {
  $<HTMLInputElement>('#room-input').value = room;
  $<HTMLSelectElement>('#gameplay').value = gameplay;
  $<HTMLInputElement>('#server-input').value = server || '';
  $('#lobby-error').textContent = '';
  lobbyMode = mode; $('#lobby-heading').textContent = mode === 'private' ? 'Bring your crew.' : 'Join an open city.';
  $('#online-note').textContent = mode === 'private' ? 'Create a room for up to four friends. Take a driver, navigator or runner role; share jobs and a growing district.' : 'Join up to sixteen players in the shared city on this server. Every crew member can help the active job. This is a development beta.';
  $('#room-field').classList.toggle('hidden', mode === 'public'); openDialog('#lobby-dialog');
}
$('#play-private').addEventListener('click', () => showLobby('private'));
$('#play-online').addEventListener('click', () => showLobby('public'));
$('#lobby-form').addEventListener('submit', event => {
  event.preventDefault(); const room = $<HTMLInputElement>('#room-input').value.trim().toUpperCase();
  const server = validateServerUrl($<HTMLInputElement>('#server-input').value);
  if (!server) { $('#lobby-error').textContent = 'Enter a secure WSS or HTTPS game server address without passwords or query parameters. Local development also accepts ws://localhost.'; $<HTMLInputElement>('#server-input').focus(); return; }
  currentServer = server;
  try { localStorage.setItem('andolan.server', server); } catch { /* This connection still works. */ }
  begin(lobbyMode, room || undefined, $<HTMLSelectElement>('#gameplay').value === 'story' ? 'story' : 'freeroam');
});
function returnTitle() {
  connection?.close(); connection = undefined; playing = false; connected = false; releaseControls(); subtitleQueue = []; audio.update(0, false);
  audio.setActivity(false); audioPosition = undefined; view.setObjectiveTarget(null);
  document.querySelectorAll<HTMLDialogElement>('dialog[open]').forEach(d => d.close());
  $('#hud').classList.add('hidden'); $('#title').classList.remove('hidden'); $('#subtitle').classList.add('hidden');
  $('#story-label').textContent = hasSave() ? 'Continue story' : 'Begin story';
  updateServerAvailability();
  playerId = 'preview'; snapshot = preview.snapshot();
  (view as typeof view & { setOverview?: (value: boolean) => void }).setOverview?.(true);
}
$('#return-title').addEventListener('click', returnTitle);
$('#about-open').addEventListener('click', () => openDialog('#about-dialog'));
document.querySelectorAll('.settings-open').forEach(b => b.addEventListener('click', () => openDialog('#settings-dialog')));
function persistSettings() { try { localStorage.setItem('andolan.settings', JSON.stringify(settings)); } catch { /* Optional preferences. */ } }
function updateServerAvailability() {
  $('#server-availability').textContent = currentServer ? 'Game server configured · choose a room to connect.' : 'Online needs a crew server. City practice is ready to play here.';
}
function updateSoundLabel() {
  $('#sound').textContent = audio.muted ? 'Enable sound' : 'Mute sound';
  $('#sound').setAttribute('aria-pressed', String(!audio.muted));
  $('#sound-quick').textContent = audio.muted ? 'Sound off' : 'Sound on';
  $('#sound-quick').setAttribute('aria-label', audio.muted ? 'Enable city sound' : 'Mute city sound');
  $('#sound-quick').setAttribute('aria-pressed', String(!audio.muted));
  $('#sound-status').textContent = audio.muted ? 'Sound is off. Test a short sample at your chosen volume.' : 'Sound is enabled. Menus pause the city; Test sound previews your volume.';
}
$<HTMLSelectElement>('#quality').value = settings.quality;
$<HTMLInputElement>('#comfort').checked = settings.comfort;
$<HTMLInputElement>('#captions').checked = settings.captions;
$<HTMLInputElement>('#large-text').checked = settings.largeText;
$<HTMLInputElement>('#assist').checked = settings.assist;
$<HTMLInputElement>('#music').checked = settings.music;
settings.volume = Number.isFinite(settings.volume) ? Math.max(0, Math.min(1, settings.volume)) : .65;
$<HTMLInputElement>('#volume').value = String(Math.round(settings.volume * 100));
$('#volume-value').textContent = `${Math.round(settings.volume * 100)}%`;
$('#volume').setAttribute('aria-valuetext', `${Math.round(settings.volume * 100)} percent`);
document.documentElement.style.setProperty('--scale', settings.largeText ? '1.15' : '1');
updateSoundLabel();
audio.configure({ volume: settings.volume, music: settings.music });
$('#volume').addEventListener('input', () => { settings.volume = Number($<HTMLInputElement>('#volume').value) / 100; $('#volume').setAttribute('aria-valuetext', `${Math.round(settings.volume * 100)} percent`); $('#volume-value').textContent = `${Math.round(settings.volume * 100)}%`; audio.configure({ volume: settings.volume }); persistSettings(); });
$('#music').addEventListener('change', () => { settings.music = $<HTMLInputElement>('#music').checked; audio.configure({ music: settings.music }); persistSettings(); });
$('#quality').addEventListener('change', () => { settings.quality = $<HTMLSelectElement>('#quality').value as 'low' | 'high'; view.setQuality(settings.quality); persistSettings(); });
for (const [id, key] of [['comfort', 'comfort'], ['captions', 'captions'], ['large-text', 'largeText'], ['assist', 'assist']] as const) {
  $(`#${id}`).addEventListener('change', () => { settings[key] = $<HTMLInputElement>(`#${id}`).checked; document.documentElement.style.setProperty('--scale', settings.largeText ? '1.15' : '1'); (view as typeof view & { setComfort?: (value: boolean) => void }).setComfort?.(settings.comfort); persistSettings(); });
}
async function toggleSound() { try { const muted = await audio.toggle(); settings.sound = !muted; updateSoundLabel(); persistSettings(); } catch { toast('Audio is unavailable in this browser. Visual job feedback remains available.'); } }
$('#sound').addEventListener('click', () => void toggleSound());
$('#sound-quick').addEventListener('click', () => { focusPlay(); void toggleSound(); });
$('#sound-preview').addEventListener('click', async () => {
  const button = $<HTMLButtonElement>('#sound-preview'); button.disabled = true; button.textContent = 'Playing sample…';
  try { await audio.preview(); } catch { toast('Audio preview could not start. Try again after enabling sound.'); }
  finally { button.disabled = false; button.textContent = 'Test sound'; updateSoundLabel(); }
});
function renderBindings() {
  const focusedAction = (document.activeElement as HTMLElement | null)?.dataset.binding;
  const list = $('#bindings'); list.replaceChildren();
  for (const [action, code] of Object.entries(bindings)) {
    const row = document.createElement('div'); row.className = 'setting';
    const button = document.createElement('button'); button.className = 'button quiet'; button.dataset.binding = action;
    button.textContent = bindingCapture === action ? 'Press a key…' : keyLabel(code);
    button.setAttribute('aria-label', `Change ${action} key, currently ${keyLabel(code)}`);
    button.addEventListener('click', () => { bindingCapture = action as Binding; renderBindings(); $('#binding-status').textContent = `Choose a key for ${action}. Escape cancels.`; });
    row.append(textElement('span', action), button); list.append(row);
  }
  document.querySelectorAll<HTMLElement>('[data-binding-label]').forEach(node => { node.textContent = keyLabel(bindings[node.dataset.bindingLabel as Binding]); });
  $('#movement-keys').textContent = [bindings.forward, bindings.left, bindings.back, bindings.right].map(keyLabel).join(' ');
  if (focusedAction) document.querySelector<HTMLButtonElement>(`[data-binding="${focusedAction}"]`)?.focus();
}
function saveBindings() { try { localStorage.setItem('andolan.bindings', JSON.stringify(bindings)); } catch { /* Optional preferences. */ } }
$('#bindings-reset').addEventListener('click', () => { bindings = { ...DEFAULT_BINDINGS }; bindingCapture = null; releaseControls(); saveBindings(); renderBindings(); $('#binding-status').textContent = 'Default keys restored.'; });
renderBindings();
for (const dialog of document.querySelectorAll<HTMLDialogElement>('dialog')) dialog.addEventListener('close', () => {
  // Native close is asynchronous. Clearing here can erase fresh movement pressed
  // after closing; controls were already released synchronously when opening.
  if (bindingCapture) { bindingCapture = null; renderBindings(); $('#binding-status').textContent = 'Key change cancelled.'; }
  if (playing && !modalOpen()) canvas.focus({ preventScroll: true });
});
document.addEventListener('keydown', event => {
  if (bindingCapture && $<HTMLDialogElement>('#settings-dialog').open) {
    event.preventDefault(); event.stopPropagation();
    if (event.code === 'Escape') { bindingCapture = null; renderBindings(); $('#binding-status').textContent = 'Key change cancelled.'; return; }
    const problem = bindingProblem(event.code, bindings, bindingCapture);
    if (problem) { $('#binding-status').textContent = problem; return; }
    const action = bindingCapture; bindings[action] = event.code; bindingCapture = null;
    releaseControls(); saveBindings(); renderBindings(); $('#binding-status').textContent = `${action} now uses ${keyLabel(event.code)}.`; return;
  }
  if (event.code === 'Escape' && playing && !modalOpen()) { event.preventDefault(); openDialog('#settings-dialog'); return; }
  if (!playing || modalOpen() || /INPUT|TEXTAREA|SELECT/.test((event.target as HTMLElement).tagName)) return;
  if ((event.target as HTMLElement).closest('button') && ['Space', 'Enter'].includes(event.code)) return;
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(event.code)) event.preventDefault();
  keys.add(event.code);
  if (!event.repeat && event.code === bindings.interact) interact();
  if (!event.repeat && event.code === bindings.vehicle) vehicleAction();
  if (!event.repeat && event.code === 'KeyJ') showJournal();
  if (!event.repeat && event.code === 'KeyC') view.recenterCamera();
  if (!event.repeat && event.code === 'KeyH' && currentPlayer()?.vehicleId) { audio.cue('horn'); command('signal', undefined, 'horn'); }
});
document.addEventListener('keyup', event => keys.delete(event.code));
window.addEventListener('blur', releaseControls);
document.addEventListener('visibilitychange', () => { if (document.hidden) releaseControls(); });
for (const button of document.querySelectorAll<HTMLButtonElement>('[data-touch-action]')) {
  button.addEventListener('pointerdown', event => {
    if (!playing || modalOpen()) return;
    event.preventDefault(); button.setPointerCapture(event.pointerId); touchActions.add(button.dataset.touchAction!);
  });
  for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) button.addEventListener(event, () => touchActions.delete(button.dataset.touchAction!));
}
$('#touch-vehicle').addEventListener('click', () => { vehicleAction(); focusPlay(); });
$('#touch-camera').addEventListener('click', () => { view.recenterCamera(); focusPlay(); });
const canvas = $<HTMLCanvasElement>('#world'); canvas.tabIndex = 0;
let drag = false, lastX = 0, lastY = 0;
canvas.addEventListener('pointerdown', event => { if (!playing || modalOpen()) return; canvas.focus({ preventScroll: true }); drag = true; lastX = event.clientX; lastY = event.clientY; canvas.setPointerCapture(event.pointerId); });
canvas.addEventListener('pointermove', event => { if (!drag || !playing || modalOpen()) return; view.setCamera((event.clientX - lastX) * .005, (event.clientY - lastY) * .004); lastX = event.clientX; lastY = event.clientY; });
for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(event, () => { drag = false; });
canvas.addEventListener('contextmenu', event => event.preventDefault());
let gamepadA = false, gamepadY = false;
function inputTick() {
  if (!playing || !connection || !connected) return;
  let forward = 0, turn = 0;
  let blocked = modalOpen() || document.hidden;
  const pad = navigator.getGamepads?.()[0];
  const held = (action: Binding) => actionHeld(action, bindings, keys, touchActions);
  if (!blocked) {
    forward = Number(held('forward') || keys.has('ArrowUp')) - Number(held('back') || keys.has('ArrowDown'));
    turn = Number(held('right') || keys.has('ArrowRight')) - Number(held('left') || keys.has('ArrowLeft'));
    if (pad) {
      if (Math.abs(pad.axes[1]) > .15) forward = -pad.axes[1]; if (Math.abs(pad.axes[0]) > .15) turn = pad.axes[0];
      if (Math.abs(pad.axes[2] || 0) > .15 || Math.abs(pad.axes[3] || 0) > .15) view.setCamera((pad.axes[2] || 0) * .035, (pad.axes[3] || 0) * .025);
      if (pad.buttons[0]?.pressed && !gamepadA) interact(); if (pad.buttons[3]?.pressed && !gamepadY) vehicleAction();
    }
  }
  // A discrete action can open a menu in this very tick. Stop its remaining input.
  if (modalOpen() || document.hidden) { blocked = true; forward = 0; turn = 0; }
  // Sample edges while a modal is open too: a held button must not activate on close.
  gamepadA = !!pad?.buttons[0]?.pressed; gamepadY = !!pad?.buttons[3]?.pressed;
  const yaw = view.getCameraYaw();
  let moveX = Math.sin(yaw) * forward - Math.cos(yaw) * turn;
  let moveZ = Math.cos(yaw) * forward + Math.sin(yaw) * turn;
  const length = Math.hypot(moveX, moveZ); if (length > 1) { moveX /= length; moveZ /= length; }
  const car = snapshot.vehicles.find(vehicle => vehicle.id === currentPlayer()?.vehicleId);
  const brake = !blocked && (keys.has('Space') || touchActions.has('brake') || !!pad?.buttons[1]?.pressed);
  const input: InputMessage = { type: 'input', seq: ++sequence, moveX, moveZ, forward: blocked ? 0 : driveThrottle(forward, car?.speed || 0, settings.assist), brake: !!car && brake, turn: -turn, sprint: !blocked && (keys.has('ShiftLeft') || keys.has('ShiftRight')) };
  connection.input(input);
}
setInterval(inputTick, 50);
let previousFrame = performance.now(); const frameTimes: number[] = [];
function frame(now: number) {
  const rawFrameMs = now - previousFrame;
  const dt = Math.min(.1, rawFrameMs / 1000); previousFrame = now;
  view.update(snapshot, playerId, dt);
  audio.setActivity(playing && connected && !modalOpen() && !document.hidden);
  if (playing && frameTimes.length < 10000) frameTimes.push(rawFrameMs);
  if (playing && !modalOpen() && settings.captions && now > subtitleDeadline) {
    const line = subtitleQueue.shift();
    $('#subtitle').classList.toggle('hidden', !line);
    if (line) { $('#subtitle-speaker').textContent = line.speaker; $('#subtitle-line').textContent = line.text; subtitleDeadline = now + Math.max(5000, line.text.length * 55); }
  } else if (!settings.captions || modalOpen()) $('#subtitle').classList.add('hidden');
  requestAnimationFrame(frame);
}
async function init() {
  try {
    view = await createWorld(canvas); view.setQuality(settings.quality);
    (view as typeof view & { setComfort?: (value: boolean) => void }).setComfort?.(settings.comfort);
    (view as typeof view & { setOverview?: (value: boolean) => void }).setOverview?.(true);
    $('#loading').classList.add('hidden'); $('#story-label').textContent = hasSave() ? 'Continue story' : 'Begin story'; updateServerAvailability();
    requestAnimationFrame(frame);
    const invite = new URLSearchParams(location.search), room = invite.get('room');
    if (room && /^[A-Z0-9-]{3,16}$/i.test(room)) showLobby(invite.get('mode') === 'public' ? 'public' : 'private', room.toUpperCase(), invite.get('gameplay') === 'freeroam' ? 'freeroam' : 'story', validateServerUrl(invite.get('server') || '') || currentServer);
    if (import.meta.env.DEV) Object.assign(window, { __ANDOLAN: { snapshot: () => snapshot, playerId: () => playerId, metrics: () => ({ frameTimes: [...frameTimes], quality: settings.quality, cameraYaw: view.getCameraYaw() }), audio: () => audio.diagnostics, command, cameraYaw: () => view.getCameraYaw(), connection: () => connection } });
  } catch (error) {
    $('#loading-text').textContent = 'This browser could not start the 3D renderer. Use a current browser with WebGL2 and hardware acceleration enabled.';
    console.error(error);
  }
}
window.addEventListener('pagehide', event => { connection?.close(); if (event.persisted) audio.setActivity(false); else void audio.destroy(); });
window.addEventListener('pageshow', event => { if (event.persisted && view) returnTitle(); });
void init();
