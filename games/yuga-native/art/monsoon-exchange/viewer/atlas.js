const $ = (id) => document.getElementById(id);
const localSource = /\/viewer\/(?:atlas\.js)$/.test(new URL(import.meta.url).pathname);
const base = new URL(localSource ? '../' : './', import.meta.url);
const file = (name) => new URL(name, base).href;
const projectDirectory =
  'https://github.com/occult-kranti/ANDOLAN/tree/game/yuga-hanuman-trial/games/yuga-native/art/monsoon-exchange';
if (localSource) $('home').href = projectDirectory;
const fontPath = localSource
  ? new URL('../../four-hero-motion/viewer/fonts/', import.meta.url)
  : new URL('../ember-rite/four-hero-motion/viewer/fonts/', import.meta.url);
for (const [family, path, weight] of [
  ['Atlas Barlow', 'barlow-condensed-latin-600-normal.woff2', '600'],
  ['Atlas DM', 'dm-sans-latin-400-normal.woff2', '400'],
]) {
  if ('FontFace' in window) {
    const face = new FontFace(family, `url("${new URL(path, fontPath).href}")`, {
      weight,
      display: 'swap',
    });
    document.fonts.add(face);
    face.load().catch(() => {});
  }
}
for (const el of document.querySelectorAll('[data-asset]')) {
  el.setAttribute(el.tagName === 'IMG' ? 'src' : 'href', file(el.dataset.asset));
}

const locations = {
  overview: {
    name: 'Entire district',
    detail:
      'The east arcade climbs to Sun Court. Dyers’ Passage drops to Indigo Cistern. The gate between them gives either side a way to change course.',
  },
  'sun-court': {
    id: 'a',
    sign: 'A',
    name: 'Sun Court',
    detail:
      'The copper trading court stands above the wet streets. The outer arcade and the narrower ledger gallery reach the same ritual floor from different heights.',
  },
  'indigo-cistern': {
    id: 'b',
    sign: 'B',
    name: 'Indigo Cistern',
    detail:
      'The west court follows the old dye works. Dyers’ Passage and the sluice enter the low court independently. The runnel leaves dry footing beside the water.',
  },
  'weavers-gate': {
    id: 'mid',
    sign: 'M',
    name: 'Weavers’ Gate',
    detail:
      'Offset loom screens break the view across the central gate. Turn toward the raised ledger route or descend through the sluice to the dye quarter.',
  },
};
const materials = {
  clay: '#d7b396',
  chalk: '#d7cbb0',
  sunstone: '#d6a96c',
  basalt: '#9ea8b9',
  jade: '#9db5a4',
};
let place = 'overview',
  mode = 'plan',
  survey,
  geometry,
  orbit,
  orbitLoad,
  transitionNumber = 0;
const plan = $('plan');
function el(name, attributes, parent, text) {
  const node = document.createElementNS('http://www.w3.org/2000/svg', name);
  for (const [k, v] of Object.entries(attributes || {})) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  parent.append(node);
  return node;
}
const coordinates = (arr) => arr.map(([x, y]) => `${x},${-y}`).join(' ');
function rectangle(parent, center, size, data) {
  return el(
    'rect',
    {
      x: center[0] - size[0] / 2,
      y: -center[1] - size[1] / 2,
      width: size[0],
      height: size[1],
      ...data,
    },
    parent,
  );
}
function status(message = '', tour = false) {
  $('load-state').textContent = message;
  if (tour) {
    const film = document.createElement('a');
    film.href = file('film/district-tour.mp4');
    film.textContent = 'Watch the filmed tour';
    $('load-state').append(' ', film, '.');
  }
  $('load-state').hidden = !message;
}
function json(path) {
  return fetch(file(path)).then((reply) => {
    if (!reply.ok) throw new Error(`Unable to load ${path}`);
    return reply.json();
  });
}
function label(parent, [x, y], text, attrs = {}) {
  return el('text', { x, y: -y, ...attrs }, parent, text);
}
function drawPlan() {
  const defs = el('defs', {}, plan);
  const grid = el(
    'pattern',
    { id: 'small-grid', width: 5, height: 5, patternUnits: 'userSpaceOnUse' },
    defs,
  );
  el('path', { d: 'M5 0H0V5', fill: 'none', stroke: '#b5ad99', 'stroke-width': '.12' }, grid);
  el('rect', { x: -300, y: -300, width: 600, height: 600, fill: 'url(#small-grid)' }, plan);
  const floors = el('g', { 'aria-hidden': 'true' }, plan);
  for (const f of geometry.floors) {
    el('polygon', { points: coordinates(f.vertices), fill: materials[f.material] || '#c5bda6' }, floors);
  }
  for (const w of survey.water) rectangle(floors, w.center, w.size, { fill: '#5b8a8c' });
  const walls = el('g', { class: 'boundary', 'aria-hidden': 'true' }, plan);
  for (const wall of geometry.walls) {
    el('line', { x1: wall.a[0], y1: -wall.a[1], x2: wall.b[0], y2: -wall.b[1] }, walls);
  }
  const lines = el(
    'g',
    {
      id: 'map-routes',
      fill: 'none',
      stroke: '#684c39',
      'stroke-width': '.35',
      'stroke-dasharray': '1.1 .7',
      'stroke-linejoin': 'round',
      'aria-hidden': 'true',
    },
    plan,
  );
  for (const link of survey.links) el('polyline', { points: coordinates(link.points) }, lines);
  const covers = el('g', { id: 'map-covers', 'aria-hidden': 'true' }, plan);
  for (const c of survey.covers) {
    const node = rectangle(covers, c.center, c.size, {
      fill: '#534d44',
      stroke: '#f2eadb',
      'stroke-width': '.17',
    });
    el('title', {}, node, c.name);
  }
  for (const obj of survey.objectives) {
    el(
      'circle',
      {
        cx: obj.center[0],
        cy: -obj.center[1],
        r: obj.radius,
        fill: 'none',
        stroke: '#fcf0cd',
        'stroke-width': '.8',
      },
      plan,
    );
  }
  const names = el('g', { 'aria-hidden': 'true' }, plan);
  const marked = new Set(Object.values(locations).map((loc) => loc.id));
  for (const room of survey.rooms.filter((r) => !marked.has(r.id))) {
    label(names, [room.center[0], room.center[1] - 0.7], room.name, { class: 'room-label' });
  }
  el('rect', { id: 'selection-ring', class: 'rim', visibility: 'hidden', 'aria-hidden': 'true' }, plan);
  for (const [key, loc] of Object.entries(locations)) {
    if (!loc.id) continue;
    const r = survey.rooms.find((room) => room.id === loc.id);
    const width = loc.id === 'mid' ? 14.8 : 15.4;
    const tag = el(
      'g',
      {
        class: 'map-tag',
        role: 'button',
        tabindex: '0',
        'aria-label': `Inspect ${loc.name}`,
        'data-pick': key,
        'aria-pressed': 'false',
        transform: `translate(${r.center[0]} ${-r.center[1]})`,
      },
      plan,
    );
    el('title', {}, tag, loc.name);
    el('rect', { x: -width / 2, y: -2.4, width, height: 4.8, rx: 0.2 }, tag);
    el(
      'text',
      { x: 0, y: 0.9 },
      tag,
      loc.id === 'mid' ? 'MID · GATE' : `${loc.sign} · ${loc.id === 'a' ? 'SUN' : 'INDIGO'}`,
    );
    tag.addEventListener('click', () => chooseLocation(key));
    tag.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        chooseLocation(key);
      }
    });
  }
  // The same survey-metre coordinate system locates the north mark and scale bar.
  const [minX, minY, maxX, maxY] = survey.bounds;
  const north = el('g', { 'aria-hidden': 'true' }, plan);
  el(
    'path',
    {
      d: `M${maxX - 6} ${-maxY + 14}v-8l-1.3 2.2m1.3-2.2 1.3 2.2`,
      stroke: '#65503b',
      'stroke-width': '.43',
      fill: 'none',
    },
    north,
  );
  label(north, [maxX - 6, maxY - 4], 'N', { class: 'map-detail', 'text-anchor': 'middle' });
  const start = minX + 3,
    vertical = -minY - 4;
  el(
    'path',
    { d: `M${start} ${vertical - 1}v1h10v-1`, stroke: '#504637', 'stroke-width': '.48', fill: 'none' },
    north,
  );
  el(
    'text',
    { x: start + 5, y: vertical - 1.7, class: 'map-detail', 'text-anchor': 'middle' },
    north,
    '10 m',
  );
  updateLayers();
  drawDetails();
}
function updateLayers() {
  $('map-routes')?.setAttribute('visibility', $('route-layer').checked ? 'visible' : 'hidden');
  $('map-covers')?.setAttribute('visibility', $('cover-layer').checked ? 'visible' : 'hidden');
}
function addFact(name, value) {
  const row = document.createElement('div'),
    term = document.createElement('dt'),
    definition = document.createElement('dd');
  term.textContent = name;
  definition.textContent = value;
  row.append(term, definition);
  $('place-facts').append(row);
}
function drawDetails() {
  const loc = locations[place],
    room = survey?.rooms.find((item) => item.id === loc.id);
  $('place-name').textContent = loc.name;
  $('place-copy').textContent = loc.detail;
  $('place-facts').replaceChildren();
  if (!survey) return;
  const [minX, minY, maxX, maxY] = survey.bounds;
  if (room) {
    plan.setAttribute('viewBox', `${room.center[0] - 30} ${-room.center[1] - 29.5} 60 59`);
    $('selection-ring')?.setAttribute('visibility', 'visible');
    const ring = $('selection-ring');
    const [wide, deep] = room.size;
    if (ring)
      for (const [key, value] of Object.entries({
        x: room.center[0] - wide / 2 - 0.7,
        y: -room.center[1] - deep / 2 - 0.7,
        width: wide + 1.4,
        height: deep + 1.4,
      }))
        ring.setAttribute(key, value);
    addFact('Floor', `${room.z > 0 ? '+' : ''}${room.z} m`);
    addFact('Room', `${wide} × ${deep} m`);
    const edges = survey.links.filter((link) => link.from === room.id || link.to === room.id);
    const entered = survey.entries.filter((entry) => entry.site === room.id);
    addFact('Entrances', String(entered.length || edges.length));
    const disk = survey.objectives.find((o) => o.room === room.id);
    if (disk) addFact('Ritual disc', `${disk.radius} m radius`);
    addFact('Connections', edges.map((e) => e.name).join(' · '));
  } else {
    plan.setAttribute('viewBox', `${minX - 3} ${-maxY - 3} ${maxX - minX + 6} ${maxY - minY + 6}`);
    $('selection-ring')?.setAttribute('visibility', 'hidden');
    addFact('Survey frame', `${maxX - minX} × ${maxY - minY} m`);
    addFact('Courts and rooms', String(survey.rooms.length));
    addFact('Connections', String(survey.links.length));
    const levels = survey.rooms.map((r) => r.z);
    addFact('Floor range', `${Math.min(...levels)} to +${Math.max(...levels)} m`);
  }
  for (const tag of plan.querySelectorAll('[data-pick]'))
    tag.setAttribute('aria-pressed', String(tag.dataset.pick === place));
}
function chooseLocation(key) {
  if (!locations[key]) return;
  closeWalk();
  place = key;
  $('location').value = key;
  drawDetails();
  if (mode === 'still') updateStill();
  if (mode === 'orbit' && orbit) orbit.aim(place);
}
function updateStill() {
  const img = $('still');
  img.alt = `Blender camera study of ${locations[place].name}`;
  const src = file(`renders/${place}.webp`);
  if (img.src !== src || (img.complete && !img.naturalWidth)) img.src = src;
}
function display(modeName) {
  $('plan-surface').hidden = modeName !== 'plan';
  $('render-surface').hidden = modeName !== 'still';
  $('orbit-surface').hidden = modeName !== 'orbit';
  $('plan-layers').hidden = modeName !== 'plan';
  $('orbit-controls').hidden = modeName !== 'orbit';
  $('orbit-help').hidden = modeName !== 'orbit';
  $('surface-note').textContent = {
    plan: 'Measured floorplan · North up',
    still: 'Blender camera · Rendered view',
    orbit: 'Editable model · Interactive orbit',
  }[modeName];
}
async function chooseMode(next) {
  closeWalk();
  const serial = ++transitionNumber;
  mode = next;
  status();
  for (const b of document.querySelectorAll('[data-mode]'))
    b.setAttribute('aria-pressed', String(b.dataset.mode === next));
  if (next !== 'orbit') {
    orbit?.activate(false);
    display(next);
    if (next === 'still') updateStill();
    if (next === 'plan' && !geometry)
      status(
        planError
          ? 'The survey could not load. Open the measured drawing below.'
          : 'Opening the measured plan…',
      );
    return;
  }
  if (!orbit) {
    display('still');
    updateStill();
    status('Opening 3D…');
    try {
      if (!orbitLoad) {
        orbitLoad = Promise.all([import('./orbit.js'), json('scene/scene-register.json')]).then(
          ([module, register]) =>
            module.createOrbit(
              $('orbit-surface'),
              file('scene/monsoon-exchange.glb'),
              register,
              (value) => {
                if (mode === 'orbit') status(`Opening 3D · ${Math.round(value * 100)}%`);
              },
              () => {
                orbit = null;
                orbitLoad = null;
                if (mode === 'orbit') {
                  chooseMode('still');
                  status('3D was interrupted. Explore the floorplan or open the model below.', true);
                }
              },
            ),
        );
      }
      orbit = await orbitLoad;
    } catch {
      orbitLoad = null;
      if (serial === transitionNumber) {
        chooseMode('still');
        status('3D could not open. Explore the floorplan or download the model below.', true);
      }
      return;
    }
  }
  if (serial !== transitionNumber || mode !== 'orbit') return;
  status();
  display('orbit');
  orbit.activate(true);
  orbit.aim(place);
}
$('route-layer').addEventListener('change', updateLayers);
$('cover-layer').addEventListener('change', updateLayers);
$('location').addEventListener('change', (event) => chooseLocation(event.target.value));
for (const button of document.querySelectorAll('[data-mode]'))
  button.addEventListener('click', () => chooseMode(button.dataset.mode));
for (const button of document.querySelectorAll('[data-shot]'))
  button.addEventListener('click', () => {
    chooseLocation(button.dataset.shot);
    chooseMode('still');
    const control = $('location');
    control.focus({ preventScroll: true });
    $('atlas').scrollIntoView({ block: 'start' });
  });
$('turn-model').addEventListener('click', () => orbit?.move(0.3));
$('zoom-in').addEventListener('click', () => orbit?.move(0, 0, 0.82));
$('zoom-out').addEventListener('click', () => orbit?.move(0, 0, 1.22));
$('reset-camera').addEventListener('click', () => orbit?.aim(place));
const motion = matchMedia('(prefers-reduced-motion: reduce)');
let walkOpen = false,
  routesPromise,
  route,
  elapsed = 0,
  playing = false,
  tickId = 0,
  previousTime = 0;
function closeWalk() {
  if (!walkOpen) return;
  walkOpen = false;
  pauseWalk();
  route = null;
  orbit?.endWalk();
  $('walk-panel').hidden = true;
  $('open-walk').setAttribute('aria-expanded', 'false');
  display(mode);
}
function updateWalkButton() {
  if (!route) return;
  const atEnd = elapsed >= route.walk_s;
  $('walk-play').textContent = motion.matches
    ? atEnd
      ? 'Return to start'
      : 'Advance 5 m'
    : playing
      ? 'Pause walk'
      : atEnd
        ? 'Replay walk'
        : elapsed
          ? 'Resume walk'
          : 'Start walk';
}
function pauseWalk() {
  playing = false;
  cancelAnimationFrame(tickId);
  updateWalkButton();
}
function seekWalk(seconds) {
  if (!route) return;
  elapsed = Math.max(0, Math.min(route.walk_s, seconds));
  const fraction = elapsed / route.walk_s;
  orbit.seekWalk(fraction);
  $('walk-time').value = elapsed;
  const report = `${Math.round(route.length_3d_m * fraction)} / ${Math.round(route.length_3d_m)} m · ${elapsed.toFixed(1)} s`;
  $('walk-readout').textContent = report;
  $('walk-time').setAttribute('aria-valuetext', report);
  updateWalkButton();
}
function chooseWalk(id, routes) {
  pauseWalk();
  route = routes.find((candidate) => candidate.id === id) || routes[0];
  $('walk-route').value = route.id;
  $('walk-time').max = route.walk_s;
  orbit.beginWalk(route, survey.rules.standing_eye_m);
  seekWalk(0);
  walkHelp();
}
function walkHelp() {
  const travel = `Eyes ${survey.rules.standing_eye_m} m above the floor. At ${survey.rules.walk_m_s} m/s this approach takes ${route.walk_s.toFixed(1)} s.`;
  $('walk-help').textContent =
    `${travel} ${motion.matches ? 'Step forward or scrub the route.' : 'Scrub to inspect any point.'}`;
}
async function openWalk() {
  if (mode !== 'orbit' || !orbit || walkOpen) return;
  walkOpen = true;
  $('open-walk').setAttribute('aria-expanded', 'true');
  try {
    routesPromise ??= json('plan/metrics.json').then((metrics) =>
      metrics.routes.filter((r) => r.rooms[0] === 'atk' && ['a', 'b'].includes(r.rooms.at(-1))),
    );
    const routes = await routesPromise;
    if (!routes.length || !survey) throw new Error('Walk data is unavailable');
    if (!walkOpen || mode !== 'orbit') return;
    const select = $('walk-route');
    if (!select.options.length) {
      for (const r of routes) select.add(new Option(r.name, r.id));
      select.addEventListener('change', () => chooseWalk(select.value, routes));
    }
    $('orbit-help').hidden = true;
    $('orbit-controls').hidden = true;
    $('walk-panel').hidden = false;
    $('surface-note').textContent = 'Guided approach · Standing eye height';
    const room = locations[place].id;
    chooseWalk(routes.find((r) => r.rooms.at(-1) === room)?.id, routes);
    select.focus({ preventScroll: true });
    status();
  } catch {
    routesPromise = undefined;
    if (walkOpen) {
      closeWalk();
      status('Route data could not open. The orbit view is available.');
    }
  }
}
function advanceWalk(now) {
  if (!playing || !route) return;
  seekWalk(elapsed + (now - previousTime) / 1000);
  previousTime = now;
  if (elapsed >= route.walk_s) pauseWalk();
  else tickId = requestAnimationFrame(advanceWalk);
}
$('open-walk').addEventListener('click', openWalk);
$('walk-play').addEventListener('click', () => {
  if (!route) return;
  if (motion.matches) {
    seekWalk(elapsed >= route.walk_s ? 0 : elapsed + (5 / route.length_3d_m) * route.walk_s);
  } else if (playing) pauseWalk();
  else {
    if (elapsed >= route.walk_s) seekWalk(0);
    playing = true;
    previousTime = performance.now();
    updateWalkButton();
    tickId = requestAnimationFrame(advanceWalk);
  }
});
$('walk-time').addEventListener('input', (e) => {
  pauseWalk();
  seekWalk(Number(e.target.value));
});
$('walk-exit').addEventListener('click', () => {
  closeWalk();
  orbit?.aim(place);
  $('open-walk').focus({ preventScroll: true });
});
document.addEventListener('visibilitychange', () => {
  if (document.hidden) pauseWalk();
});
motion.addEventListener('change', () => {
  if (walkOpen && route) {
    pauseWalk();
    walkHelp();
  }
});
$('still').addEventListener('error', () => {
  if (mode === 'still' && !$('load-state').querySelector('a'))
    status('This Blender view could not load. The measured drawing is available below.', true);
});
let planError = false;
status('Opening the measured plan…');
Promise.all([json('plan/survey.json'), json('plan/geometry.json')])
  .then(([data, shapes]) => {
    survey = data;
    geometry = shapes;
    drawPlan();
    if (mode === 'plan') status();
  })
  .catch(() => {
    planError = true;
    if (mode === 'plan') status('The survey could not load. Open the measured drawing below.');
  });
