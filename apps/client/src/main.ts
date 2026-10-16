import './style.css';
import { createWorld } from './world/index';
import { connectSolo, connectOnline, hasSave, type Connection } from './connection';
import { GameAudio } from './audio';
import { Simulation } from '../../../packages/sim/src/index';
import { WORLD, landmark } from '../../../packages/sim/src/world';
import { CAMPAIGN, EVIDENCE, getChoiceConsequence, getDocumentStatus } from '../../../packages/content/src/index';
import type { Snapshot, PlayerSnapshot, InputMessage, CommandAction } from '../../../packages/protocol/src/index';

const $ = <T extends HTMLElement = HTMLElement>(selector: string) => document.querySelector<T>(selector)!;
const app = $('#app');
app.innerHTML = `
  <div class="title-screen" id="title">
    <header class="masthead"><div class="masthead-name"><span class="brandmark">A</span> An original city story</div><span class="build-tag">First Edition · Playable preview 0.1</span></header>
    <section class="title-body">
      <p class="eyebrow title-location">Devnagar. After the rain.</p>
      <h1 class="display">ANDOLAN</h1><h2 class="display">City of Consequences</h2>
      <p class="title-description">One delivery. Two versions of the truth.<br>Find your way through a city on the edge of change — and decide what comes after.</p>
      <nav class="play-menu" aria-label="Play modes">
        <button class="button primary play-main" id="play-story"><span><span id="story-label">Begin story</span><small>Solo · saved on this device</small></span><span class="arrow"><svg viewBox="0 0 24 24" width="21" height="21" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M6 18 18 6M6 6h12v12"/></svg></span></button>
        <div class="secondary-actions"><button class="button" id="play-private">Private crew <svg viewBox="0 0 24 24" width="21" height="21" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M6 18 18 6M6 6h12v12"/></svg></button><button class="button" id="play-online">City sandbox <svg viewBox="0 0 24 24" width="21" height="21" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M6 18 18 6M6 6h12v12"/></svg></button></div>
      </nav>
    </section>
    <div class="scene-credit"><span class="line"></span><p>01 / OLD MARKET<br><span>A fictional city. Your choices.</span></p></div>
    <footer class="title-foot"><p><strong>Explore. Drive. Listen. Choose.</strong><br>Six connected missions in an original 3D district.</p><div class="title-controls"><button class="small-link settings-open">Settings</button><button class="small-link" id="about-open">About this build</button></div></footer>
  </div>
  <main class="hud hidden" id="hud" aria-label="Game controls">
    <div class="hud-top"><section class="mission" aria-label="Current objective"><p class="eyebrow" id="chapter-label">Chapter 01 / 06</p><h2 id="mission-title">Last Delivery</h2><p id="objective">Meet Yusuf at the garage.</p><span class="mission-distance" id="mission-distance"></span><div class="chapter-count" id="chapter-count"></div><button id="vote-status" class="vote-status hidden"></button></section>
    <div class="room-bar"><div class="room-status"><i class="status-dot" id="status-dot"></i><span id="status-text">Story</span></div><button id="reconnect" class="button recovery hidden">Reconnect</button><div class="room-tools"><button class="icon-button" id="journal-open" aria-label="Open evidence journal" title="Evidence journal (J)">▤</button><button class="icon-button" id="crew-open" aria-label="Room and crew" title="Room and crew">♧</button><button class="icon-button settings-open" aria-label="Open settings" title="Settings (Escape)">⚙</button></div><p class="crew" id="crew-count"></p></div></div>
    <div class="hud-bottom"><div class="map-wrap"><canvas id="minimap" width="308" height="308" aria-label="District map with your position and objective"></canvas><div class="map-caption"><span>Old Market</span><span>N ↑</span></div></div><div class="street"><h3 id="street-name">Yusuf’s Garage</h3><p id="street-subtitle">DEVNAGAR / MONSOON EVENING</p></div></div>
    <button class="interaction hidden" id="interact"><span class="key">E</span><span id="interact-text">Talk to Yusuf</span></button>
    <div class="driving hidden" id="driving"><div class="speed" id="speed">0</div><span>KM/H · <span id="seat-name">DRIVER</span></span></div>
    <div class="control-strip"><span><span class="key">W A S D</span> Move</span><span><span class="key">F</span> Vehicle</span><span><span class="key">Drag</span> Look</span><span><span class="key">Esc</span> Menu</span></div>
    <div class="subtitle hidden" id="subtitle" aria-live="polite"><strong id="subtitle-speaker"></strong><p id="subtitle-line"></p></div>
    <div class="touch-controls" aria-label="Touch movement"><button class="up" data-key="KeyW" aria-label="Move forward">↑</button><button class="left" data-key="KeyA" aria-label="Move left">←</button><button class="down" data-key="KeyS" aria-label="Move backward">↓</button><button class="right" data-key="KeyD" aria-label="Move right">→</button></div>
  </main>
  <div id="toast" class="toast hidden" role="status"></div>
  <div id="loading" class="loading"><h2>ANDOLAN</h2><div class="loading-track"></div><p id="loading-text">Building the streets of Devnagar…</p></div>
  <dialog id="settings-dialog" aria-labelledby="settings-heading"><header class="dialog-header"><div><p class="eyebrow">Make yourself at home</p><h2 id="settings-heading">Settings & controls</h2></div><button class="close" data-close aria-label="Close settings">×</button></header><div class="dialog-body">
    <div class="setting"><label for="quality">Graphics<small>Low reduces shadows, detail and rendering resolution.</small></label><select id="quality"><option value="high">High</option><option value="low">Low</option></select></div>
    <div class="setting"><label for="comfort">Comfort camera<small>Gentler camera response; no dramatic camera motion.</small></label><input id="comfort" type="checkbox"></div>
    <div class="setting"><label for="captions">Subtitles<small>Full conversations also remain in mission interactions.</small></label><input id="captions" type="checkbox" checked></div>
    <div class="setting"><label for="large-text">Larger dialog text</label><input id="large-text" type="checkbox"></div>
    <div class="setting"><label for="sound">City ambience<small>Original synthesized rain and engine. Off until you enable it.</small></label><button id="sound" class="button quiet">Enable sound</button></div>
    <div class="setting"><label for="assist">Driving assistance<small>Caps acceleration for easier cornering.</small></label><input id="assist" type="checkbox"></div>
    <div class="controls-table"><div><span class="key">WASD / ↑↓←→</span> Move / drive</div><div><span class="key">Shift</span> Sprint</div><div><span class="key">E</span> Interact</div><div><span class="key">F</span> Enter / exit car</div><div><span class="key">Drag</span> Orbit camera</div><div><span class="key">J</span> Evidence</div></div>
    <p class="muted" style="font-size:11px;margin-top:17px">Gamepad: left stick to move or steer, right stick to look, A to interact, Y to enter or exit. Online rooms continue while this menu is open; your input stops.</p>
    <details style="margin-top:17px"><summary>Rebind keyboard controls</summary><div id="bindings"></div></details>
  </div><footer class="dialog-footer"><button class="button quiet" id="return-title">Return to title</button><button class="button primary" data-close>Continue</button></footer></dialog>
  <dialog id="lobby-dialog" aria-labelledby="lobby-heading"><header class="dialog-header"><div><p class="eyebrow" id="lobby-eyebrow">A city is better with company</p><h2 id="lobby-heading">Private crew</h2></div><button class="close" data-close aria-label="Close lobby">×</button></header><form id="lobby-form"><div class="dialog-body"><p class="online-note" id="online-note">Create an invited room for up to four players. Your story belongs to this room and is saved on the server.</p><div class="field"><label for="player-name">Your name in the crew</label><input id="player-name" value="Aadi" maxlength="24" required autocomplete="off"></div><div class="field" id="room-field"><label for="room-input">Room code <span class="muted">(optional)</span></label><input id="room-input" placeholder="Leave blank to create a room" maxlength="16" pattern="[A-Za-z0-9\\x2d]{3,16}" autocomplete="off"><small>Share a room code with friends to play together.</small></div><p class="muted" style="font-size:11px">A running ANDOLAN server is required. Downloaded standalone copies support solo Story. Public matchmaking and permanent accounts are not part of this preview.</p></div><footer class="dialog-footer"><button class="button primary" type="submit">Enter the city <svg viewBox="0 0 24 24" width="21" height="21" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M6 18 18 6M6 6h12v12"/></svg></button></footer></form></dialog>
  <dialog id="mission-dialog" aria-labelledby="dialog-mission-title"><header class="dialog-header"><div><p class="eyebrow" id="dialog-location">Devnagar</p><h2 id="dialog-mission-title">Last Delivery</h2></div><button class="close" data-close aria-label="Close conversation">×</button></header><div class="dialog-body"><div id="dialogue-lines" class="dialogue-lines"></div><div id="choice-list" class="choice-list"></div><p class="vote-note" id="vote-note"></p></div><footer class="dialog-footer"><button class="button primary" id="dialog-continue">Continue</button></footer></dialog>
  <dialog id="journal-dialog" aria-labelledby="journal-heading"><header class="dialog-header"><div><p class="eyebrow">The newsroom / case notes</p><h2 id="journal-heading">What we know</h2></div><button class="close" data-close aria-label="Close journal">×</button></header><div class="dialog-body"><p class="muted" style="font-size:12px">A discrepancy is a question. Keep the record beside the claim.</p><div id="evidence-list"></div></div><footer class="dialog-footer"><button class="button primary" data-close>Back to the city</button></footer></dialog>
  <dialog id="crew-dialog" aria-labelledby="crew-heading"><header class="dialog-header"><div><p class="eyebrow">Together in Devnagar</p><h2 id="crew-heading">Your crew</h2></div><button class="close" data-close aria-label="Close crew">×</button></header><div class="dialog-body"><p id="crew-description"></p><div id="crew-recap"></div><div id="room-code" class="room-code"></div><div id="crew-list"></div><p class="muted" style="font-size:11px;margin-top:16px">Preset signals only. Private codes are invitations: share them with people you trust. This preview has no public accounts or economy.</p></div><footer class="dialog-footer"><button class="button" id="signal-ready">Signal: ready</button><button class="button primary" id="copy-invite">Copy invite</button></footer></dialog>
  <dialog id="ending-dialog" aria-labelledby="ending-heading"><header class="dialog-header"><div><p class="eyebrow">First Edition / epilogue</p><h2 id="ending-heading">A city, changed</h2></div><button class="close" data-close aria-label="Return to free roam">×</button></header><div class="dialog-body"><p class="eyebrow">Your story ends with</p><h3 class="ending-title" id="ending-title"></h3><p class="ending-copy" id="ending-copy"></p><div id="ending-history"></div><p class="muted" style="font-size:11px;margin-top:22px">You completed this condensed six-mission preview. The full 22-mission campaign and further districts are in development.</p></div><footer class="dialog-footer"><button class="button" id="replay">Start a new story</button><button class="button primary" data-close>Keep exploring</button></footer></dialog>
  <dialog id="about-dialog" aria-labelledby="about-heading"><header class="dialog-header"><div><p class="eyebrow">Playable preview 0.1</p><h2 id="about-heading">City of Consequences</h2></div><button class="close" data-close aria-label="Close about">×</button></header><div class="dialog-body"><p>ANDOLAN is an original fictional city drama. Walk and drive through Old Market, investigate conflicting records, and choose what accountable change looks like.</p><p>This build contains six connected missions, original procedural city art, local story saves, real server rooms and branching endings. It is an early playable release, with a larger city and campaign planned.</p><p class="muted">Characters, institutions and events are invented. Engine: PlayCanvas. All game art and synthesized audio are original. REA was used to inspect a permissively licensed controller reference; no commercial game code or assets are included.</p><p class="muted">Desktop Chromium with WebGL2 is the primary test environment. Touch controls are provided. Full mobile performance and public service capacity are still to be validated.</p></div><footer class="dialog-footer"><button class="button primary" data-close>Back</button></footer></dialog>
`;

type Binding = 'forward' | 'back' | 'left' | 'right' | 'interact' | 'vehicle';
const defaultBindings: Record<Binding, string> = { forward: 'KeyW', back: 'KeyS', left: 'KeyA', right: 'KeyD', interact: 'KeyE', vehicle: 'KeyF' };
let bindings = { ...defaultBindings };
let settings = { quality: 'high' as 'high' | 'low', comfort: matchMedia('(prefers-reduced-motion: reduce)').matches, captions: true, largeText: false, assist: false };
try { settings = { ...settings, ...JSON.parse(localStorage.getItem('andolan.settings') || '{}') }; bindings = { ...bindings, ...JSON.parse(localStorage.getItem('andolan.bindings') || '{}') }; } catch { /* Defaults remain usable. */ }
let view: Awaited<ReturnType<typeof createWorld>>;
let connection: Connection | undefined;
let snapshot: Snapshot;
let playerId = 'preview';
let playing = false, local = true, connected = false, lobbyMode: 'private' | 'public' = 'private';
let sequence = Date.now(), commandSequence = 0, toastTimer = 0, lastStage = '', endingShown = false;
let lastHistoryLength = -1;
let subtitleStageQueued = '';
let hasWelcomed = false, recapOnSnapshot = false;
let interactionAction: (() => void) | undefined;
const keys = new Set<string>();
const audio = new GameAudio();
const preview = new Simulation('PREVIEW', 'private'); preview.addPlayer('preview', 'Aadi'); snapshot = preview.snapshot();
let subtitleQueue: { speaker: string; text: string }[] = [], subtitleDeadline = 0;
let bindingCapture: Binding | null = null;
function toast(message: string) { $('#toast').textContent = message; $('#toast').classList.remove('hidden'); clearTimeout(toastTimer); toastTimer = window.setTimeout(() => $('#toast').classList.add('hidden'), 5000); }
function modalOpen() { return !!document.querySelector('dialog[open]'); }
function openDialog(id: string) { keys.clear(); document.querySelectorAll<HTMLDialogElement>('dialog[open]').forEach(d => d.close()); $<HTMLDialogElement>(id).showModal(); }
document.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => button.closest('dialog')?.close()));
function command(action: CommandAction, target?: string, value?: string) { connection?.command({ type: 'command', id: `c${Date.now()}_${++commandSequence}`, action, ...(target ? { target } : {}), ...(value ? { value } : {}) }); }
function currentPlayer(): PlayerSnapshot | undefined { return snapshot.players.find(p => p.id === playerId); }
function distance(a: { x: number; z: number }, b: { x: number; z: number }) { return Math.hypot(a.x - b.x, a.z - b.z); }
function textElement(tag: string, text: string, className = '') { const e = document.createElement(tag); e.textContent = text; e.className = className; return e; }

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
  const p = currentPlayer(); if (!p || !connected) return;
  if (p.vehicleId) command('exit'); else {
    const car = [...snapshot.vehicles].sort((a, b) => distance(p, a) - distance(p, b))[0];
    if (car) command('enter', car.id);
  }
}
$('#interact').addEventListener('click', interact);

function updateHUD() {
  if (!playing) return;
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
  audio.update(car?.speed || 0, !!car);
  interactionAction = undefined;
  let prompt = '';
  if (connected) {
    if (!p.vehicleId && target && distance(p, target) <= target.radius && !m.complete && ['interact', 'choice'].includes(m.trigger)) {
      prompt = m.trigger === 'choice' ? 'Listen & choose' : `Interact · ${target.name}`;
      interactionAction = showDialogue;
    } else if (car && p.seat !== 0 && !car.occupants[0] && Math.abs(car.speed) <= 1.5) { prompt = 'Take the wheel'; interactionAction = () => command('take_wheel'); }
    else if (car) { prompt = Math.abs(car.speed) > 1 ? 'Brake to exit · S' : 'Exit vehicle'; interactionAction = vehicleAction; }
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
  for (const car of snapshot.vehicles) { c.fillStyle = '#d6ded1'; c.fillRect(cx(car.x) - 3, cz(car.z) - 3, 6, 6); }
  for (const other of snapshot.players.filter(a => a.connected && a.id !== p.id)) { c.fillStyle = '#8bd3cb'; c.beginPath(); c.arc(cx(other.x), cz(other.z), 5, 0, Math.PI * 2); c.fill(); }
  c.save(); c.translate(cx(p.x), cz(p.z)); c.rotate(-p.heading); c.fillStyle = '#fff7e5';
  c.beginPath(); c.moveTo(0, 9); c.lineTo(-6, -6); c.lineTo(0, -3); c.lineTo(6, -6); c.closePath(); c.fill(); c.restore();
}
function showJournal() {
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
  $('#crew-description').textContent = local ? 'You are playing solo. Return to the title and choose Private crew to start a shared story.' : 'Invite a friend using this room code. They must connect to the same running game server.';
  $('#room-code').textContent = local ? 'SOLO STORY' : snapshot.room;
  const list = $('#crew-list'); list.replaceChildren();
  for (const p of snapshot.players) list.append(textElement('p', `${p.name}${p.id === playerId ? ' (you)' : ''} · ${p.connected ? 'here' : 'disconnected'} · ${p.vehicleId ? (p.seat === 0 ? 'driving' : 'passenger') : 'on foot'}${p.signal ? ` · ${p.signal}` : ''}`));
  const recap = $('#crew-recap'); recap.replaceChildren(textElement('h3', snapshot.mission.title, 'display'), textElement('p', snapshot.mission.objective));
  for (const entry of snapshot.mission.history.slice(-3)) recap.append(textElement('p', getChoiceConsequence(entry), 'recap-line'));
  if (Object.keys(snapshot.mission.votes).length) recap.append(textElement('p', $('#vote-status').textContent || '', 'vote-note'));

  $<HTMLButtonElement>('#copy-invite').disabled = local;
  openDialog('#crew-dialog');
}
$('#crew-open').addEventListener('click', showCrew);
$('#vote-status').addEventListener('click', showCrew);
$('#reconnect').addEventListener('click', () => connection?.reconnect?.());
$('#copy-invite').addEventListener('click', async () => { try { const url = new URL(location.href); url.searchParams.set('room', snapshot.room); url.searchParams.set('mode', snapshot.mode); await navigator.clipboard.writeText(url.toString()); toast('Invite link copied.'); } catch { toast(`Share room code ${snapshot.room} in ${snapshot.mode === 'public' ? 'City sandbox' : 'Private crew'} on this server.`); } });
$('#signal-ready').addEventListener('click', () => { command('signal', undefined, 'ready'); toast('Ready signal sent to your room.'); });

const callbacks = {
  snapshot: (state: Snapshot) => { snapshot = state; updateHUD(); if (recapOnSnapshot) { recapOnSnapshot = false; if (state.mission.history.length > 0 && !state.mission.complete) showCrew(); } },
  welcome: (id: string, _room: string, isLocal: boolean) => { playerId = id; local = isLocal; sequence = Date.now(); recapOnSnapshot = !isLocal && !hasWelcomed; hasWelcomed = true; },
  status: (message: string, online: boolean) => { connected = online; $('#status-text').textContent = message; $('#status-dot').style.background = online ? '#bed7a6' : '#e3a25d'; $('#reconnect').classList.toggle('hidden', online || local); },
  error: toast,
};
function begin(mode: 'solo' | 'private' | 'public', room?: string) {
  connection?.close(); keys.clear(); lastStage = ''; endingShown = false; lastHistoryLength = -1; hasWelcomed = false; recapOnSnapshot = false; local = mode === 'solo';
  document.querySelectorAll<HTMLDialogElement>('dialog[open]').forEach(d => d.close());
  playing = true; connected = false; $('#title').classList.add('hidden'); $('#hud').classList.remove('hidden');
  (view as typeof view & { setOverview?: (value: boolean) => void }).setOverview?.(false);
  const name = $<HTMLInputElement>('#player-name').value.trim() || 'Aadi';
  connection = mode === 'solo' ? connectSolo(name, callbacks) : connectOnline({ type: 'join', mode, name, ...(room ? { room } : {}) }, callbacks);
}
$('#play-story').addEventListener('click', () => begin('solo'));
function showLobby(mode: 'private' | 'public', room = '') {
  $<HTMLInputElement>('#room-input').value = room;
  lobbyMode = mode; $('#lobby-heading').textContent = mode === 'private' ? 'Private crew' : 'City sandbox';
  $('#online-note').textContent = mode === 'private' ? 'Create an invited room for up to four players. Your story belongs to this room and is saved on the server.' : 'Join the shared development sandbox on this server. This is a capped test room, separate from private story saves; it is not a regional public launch.';
  $('#room-field').classList.toggle('hidden', mode === 'public'); openDialog('#lobby-dialog');
}
$('#play-private').addEventListener('click', () => showLobby('private'));
$('#play-online').addEventListener('click', () => showLobby('public'));
$('#lobby-form').addEventListener('submit', event => { event.preventDefault(); const room = $<HTMLInputElement>('#room-input').value.trim().toUpperCase(); begin(lobbyMode, room || undefined); });
function returnTitle() {
  connection?.close(); connection = undefined; playing = false; connected = false; keys.clear(); subtitleQueue = []; audio.update(0, false);
  document.querySelectorAll<HTMLDialogElement>('dialog[open]').forEach(d => d.close());
  $('#hud').classList.add('hidden'); $('#title').classList.remove('hidden'); $('#subtitle').classList.add('hidden');
  $('#story-label').textContent = hasSave() ? 'Continue story' : 'Begin story';
  playerId = 'preview'; snapshot = preview.snapshot();
  (view as typeof view & { setOverview?: (value: boolean) => void }).setOverview?.(true);
}
$('#return-title').addEventListener('click', returnTitle);
$('#about-open').addEventListener('click', () => openDialog('#about-dialog'));
document.querySelectorAll('.settings-open').forEach(b => b.addEventListener('click', () => openDialog('#settings-dialog')));
function persistSettings() { try { localStorage.setItem('andolan.settings', JSON.stringify(settings)); } catch { /* Optional preferences. */ } }
$<HTMLSelectElement>('#quality').value = settings.quality;
$<HTMLInputElement>('#comfort').checked = settings.comfort;
$<HTMLInputElement>('#captions').checked = settings.captions;
$<HTMLInputElement>('#large-text').checked = settings.largeText;
$<HTMLInputElement>('#assist').checked = settings.assist;
$('#quality').addEventListener('change', () => { settings.quality = $<HTMLSelectElement>('#quality').value as 'low' | 'high'; view.setQuality(settings.quality); persistSettings(); });
for (const [id, key] of [['comfort', 'comfort'], ['captions', 'captions'], ['large-text', 'largeText'], ['assist', 'assist']] as const) {
  $(`#${id}`).addEventListener('change', () => { settings[key] = $<HTMLInputElement>(`#${id}`).checked; document.documentElement.style.setProperty('--scale', settings.largeText ? '1.15' : '1'); (view as typeof view & { setComfort?: (value: boolean) => void }).setComfort?.(settings.comfort); persistSettings(); });
}
$('#sound').addEventListener('click', async () => { try { const muted = await audio.toggle(); $('#sound').textContent = muted ? 'Enable sound' : 'Mute sound'; } catch { toast('Audio is unavailable in this browser. Subtitles remain available.'); } });
function renderBindings() {
  const list = $('#bindings'); list.replaceChildren();
  for (const [action, code] of Object.entries(bindings)) {
    const row = document.createElement('div'); row.className = 'setting'; const b = document.createElement('button'); b.className = 'button quiet'; b.textContent = code.replace('Key', '');
    b.addEventListener('click', () => { bindingCapture = action as Binding; b.textContent = 'Press a key…'; }); row.append(textElement('label', action), b); list.append(row);
  }
}
renderBindings();
document.addEventListener('keydown', event => {
  if (bindingCapture) { event.preventDefault(); bindings[bindingCapture] = event.code; bindingCapture = null; try { localStorage.setItem('andolan.bindings', JSON.stringify(bindings)); } catch { /* Optional preferences. */ } renderBindings(); return; }
  if (event.code === 'Escape' && playing && !modalOpen()) { event.preventDefault(); openDialog('#settings-dialog'); return; }
  if (!playing || modalOpen() || /INPUT|TEXTAREA|SELECT/.test((event.target as HTMLElement).tagName)) return;
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(event.code)) event.preventDefault();
  keys.add(event.code);
  if (!event.repeat && event.code === bindings.interact) interact();
  if (!event.repeat && event.code === bindings.vehicle) vehicleAction();
  if (!event.repeat && event.code === 'KeyJ') showJournal();
});
document.addEventListener('keyup', event => keys.delete(event.code));
window.addEventListener('blur', () => keys.clear());
document.addEventListener('visibilitychange', () => { if (document.hidden) keys.clear(); });
for (const b of document.querySelectorAll<HTMLButtonElement>('[data-key]')) {
  b.addEventListener('pointerdown', e => { e.preventDefault(); b.setPointerCapture(e.pointerId); keys.add(b.dataset.key!); });
  for (const ev of ['pointerup', 'pointercancel', 'lostpointercapture']) b.addEventListener(ev, () => keys.delete(b.dataset.key!));
}
const canvas = $<HTMLCanvasElement>('#world'); let drag = false, lastX = 0, lastY = 0;
canvas.addEventListener('pointerdown', e => { if (!playing) return; drag = true; lastX = e.clientX; lastY = e.clientY; canvas.setPointerCapture(e.pointerId); });
canvas.addEventListener('pointermove', e => { if (!drag || !playing || modalOpen()) return; view.setCamera((e.clientX - lastX) * .005, (e.clientY - lastY) * .004); lastX = e.clientX; lastY = e.clientY; });
canvas.addEventListener('pointerup', () => { drag = false; }); canvas.addEventListener('pointercancel', () => { drag = false; }); canvas.addEventListener('contextmenu', e => e.preventDefault());
let gamepadA = false, gamepadY = false;
function inputTick() {
  if (!playing || !connection || !connected) return;
  let forward = 0, turn = 0;
  const blocked = modalOpen() || document.hidden;
  if (!blocked) {
    forward = Number(keys.has(bindings.forward) || keys.has('ArrowUp')) - Number(keys.has(bindings.back) || keys.has('ArrowDown'));
    turn = Number(keys.has(bindings.right) || keys.has('ArrowRight')) - Number(keys.has(bindings.left) || keys.has('ArrowLeft'));
    const pad = navigator.getGamepads?.()[0];
    if (pad) {
      if (Math.abs(pad.axes[1]) > .15) forward = -pad.axes[1]; if (Math.abs(pad.axes[0]) > .15) turn = pad.axes[0];
      if (Math.abs(pad.axes[2] || 0) > .15 || Math.abs(pad.axes[3] || 0) > .15) view.setCamera((pad.axes[2] || 0) * .035, (pad.axes[3] || 0) * .025);
      if (pad.buttons[0]?.pressed && !gamepadA) interact(); if (pad.buttons[3]?.pressed && !gamepadY) vehicleAction();
      gamepadA = !!pad.buttons[0]?.pressed; gamepadY = !!pad.buttons[3]?.pressed;
    }
  }
  const yaw = view.getCameraYaw();
  let moveX = Math.sin(yaw) * forward - Math.cos(yaw) * turn;
  let moveZ = Math.cos(yaw) * forward + Math.sin(yaw) * turn;
  const length = Math.hypot(moveX, moveZ); if (length > 1) { moveX /= length; moveZ /= length; }
  const input: InputMessage = { type: 'input', seq: ++sequence, moveX, moveZ, forward: settings.assist ? forward * .55 : forward, turn: -turn, sprint: !blocked && (keys.has('ShiftLeft') || keys.has('ShiftRight')) };
  connection.input(input);
}
setInterval(inputTick, 50);
let previousFrame = performance.now(); const frameTimes: number[] = [];
function frame(now: number) {
  const rawFrameMs = now - previousFrame;
  const dt = Math.min(.1, rawFrameMs / 1000); previousFrame = now;
  view.update(snapshot, playerId, dt);
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
    $('#loading').classList.add('hidden'); $('#story-label').textContent = hasSave() ? 'Continue story' : 'Begin story';
    requestAnimationFrame(frame);
    const invite = new URLSearchParams(location.search), room = invite.get('room');
    if (room && /^[A-Z0-9-]{3,16}$/i.test(room)) showLobby(invite.get('mode') === 'public' ? 'public' : 'private', room.toUpperCase());
    if (import.meta.env.DEV) Object.assign(window, { __ANDOLAN: { snapshot: () => snapshot, playerId: () => playerId, metrics: () => ({ frameTimes: [...frameTimes], quality: settings.quality, cameraYaw: view.getCameraYaw() }), command, cameraYaw: () => view.getCameraYaw(), connection: () => connection } });
  } catch (error) {
    $('#loading-text').textContent = 'This browser could not start the 3D renderer. Use a current browser with WebGL2 and hardware acceleration enabled.';
    console.error(error);
  }
}
window.addEventListener('pagehide', () => connection?.close());
void init();
