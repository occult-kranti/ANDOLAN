const byId = (id) => document.getElementById(id);
const make = (tag, value) => {
  const node = document.createElement(tag);
  if (value !== undefined) node.textContent = value;
  return node;
};
const groupNames = {
  room: 'Rooms',
  route: 'Routes',
  cover: 'Cover',
  artifact: 'Landmarks',
  architecture: 'Architecture',
  rite: 'Ritual objects',
};
const kindNames = {
  room: 'Room',
  route: 'Route',
  cover: 'Cover',
  artifact: 'Landmark',
  architecture: 'Architecture',
  rite: 'Ritual object',
};
const pageSize = 9;
const state = {
  catalog: null,
  concepts: null,
  kind: 'all',
  search: '',
  limit: pageSize,
  matches: [],
  selected: null,
  medium: 'render',
  opener: null,
};
const dialog = byId('detail');
const img = (src, alt) => {
  const image = make('img');
  image.loading = 'lazy';
  image.decoding = 'async';
  image.src = src;
  image.alt = alt;
  return image;
};
const link = (title, href) => {
  const a = make('a', title);
  a.href = href;
  return a;
};
async function loadJSON(file) {
  const response = await fetch(file);
  if (!response.ok) throw new Error(file);
  return response.json();
}
function conceptFile(id) {
  const catalogItem = state.concepts?.items?.[id];
  return catalogItem?.file ? './concepts/' + catalogItem.file : null;
}
function boardFor(id) {
  const related = state.concepts?.route_boards?.[id] || [];
  const boards = state.concepts?.boards || [];
  return (
    boards.find((board) => board.id === state.concepts?.items?.[id]?.board) ||
    boards.find((board) => board.items?.includes(id)) ||
    boards.find((board) => related.includes(board.id))
  );
}
function filters() {
  const bar = byId('filters');
  const kinds = [...new Set(state.catalog.elements.map((item) => item.kind))];
  for (const kind of ['all', ...kinds]) {
    const button = make('button', kind === 'all' ? 'All' : groupNames[kind] || kind);
    button.type = 'button';
    button.dataset.kind = kind;
    button.addEventListener('click', () => {
      state.kind = kind;
      state.limit = pageSize;
      renderIndex();
    });
    bar.append(button);
  }
}
function cardFor(item) {
  const card = link('', '#element=' + encodeURIComponent(item.id));
  card.className = 'study';
  card.dataset.id = item.id;
  const thumb = make('div');
  thumb.className = 'thumb';
  const art = conceptFile(item.id);
  thumb.append(
    img(art || './' + item.render, art ? item.title + ' concept art' : 'Blender views of ' + item.title),
  );
  const caption = make('div');
  caption.className = 'caption';
  const kind = make('span', kindNames[item.kind] || item.kind);
  kind.className = 'kind';
  caption.append(make('h3', item.title), kind);
  card.append(thumb, caption);
  card.addEventListener('click', (event) => {
    if (event.button || event.ctrlKey || event.shiftKey || event.altKey || event.metaKey) return;
    event.preventDefault();
    state.opener = card;
    navigateTo(item.id);
  });
  return card;
}
function renderIndex() {
  const term = state.search.toLocaleLowerCase();
  state.matches = state.catalog.elements.filter(
    (item) =>
      (state.kind === 'all' || item.kind === state.kind) &&
      (!term ||
        [item.title, item.kind, item.cue, item.art_brief].some((v) => v?.toLocaleLowerCase().includes(term))),
  );
  if (state.kind === 'all' && !term) {
    const kinds = [...new Set(state.matches.map((item) => item.kind))];
    const collections = kinds.map((kind) => state.matches.filter((item) => item.kind === kind));
    const depth = Math.max(...collections.map((group) => group.length));
    state.matches = Array.from({ length: depth }, (_, i) =>
      collections.flatMap((group) => group.slice(i, i + 1)),
    ).flat();
  }
  const total = state.catalog.elements.length,
    matches = state.matches.length;
  byId('index-count').textContent =
    matches === total ? total + ' elements' : matches + ' of ' + total + ' elements';
  byId('library').replaceChildren(...state.matches.slice(0, state.limit).map(cardFor));
  byId('library').setAttribute('aria-busy', 'false');
  for (const button of byId('filters').children)
    button.setAttribute('aria-pressed', String(button.dataset.kind === state.kind));
  byId('empty').hidden = matches > 0;
  byId('empty').textContent = 'No elements match this selection. Try another type or search term.';
  byId('more').hidden = state.limit >= matches;
}
function renderBoards() {
  const boards = state.concepts?.boards || [];
  const list = byId('board-list');
  list.replaceChildren();
  for (const board of boards) {
    const file = './concepts/' + board.file;
    const figure = make('figure'),
      a = link('', file);
    a.append(img(file, board.alt || board.title));
    figure.append(a);
    const caption = make('figcaption');
    caption.append(make('h3', board.title), link('Open board', file));
    figure.append(caption);
    list.append(figure);
  }
  if (!boards.length) list.append(make('p', 'The visual development boards could not be loaded.'));
  const cover = state.concepts?.hero;
  const file = typeof cover === 'string' ? cover : cover?.file;
  if (file) {
    byId('cover-image').src = './concepts/' + file;
    byId('cover-image').alt = cover.alt || 'Painted environment concept for Mandala Rift';
    byId('cover-caption').textContent = 'Mandala Rift · district concept';
    byId('cover-link').href = './concepts/' + file;
  }
}
function mediaFor(item) {
  const media = [
    {
      key: 'render',
      title: 'Blender views',
      file: './' + item.render,
      alt: 'Four Blender views of ' + item.title,
    },
    {
      key: 'plate',
      title: 'Scale drawing',
      file: './' + item.plate,
      alt: 'Registered scale drawing of ' + item.title,
    },
    { key: 'clip', title: 'Motion', file: './' + item.clip, alt: 'Motion study of ' + item.title },
  ];
  const art = conceptFile(item.id),
    board = boardFor(item.id);
  if (art || board)
    media.unshift({
      key: 'concept',
      title: art ? 'Concept art' : 'Concept board',
      file: art || './concepts/' + board.file,
      alt: art
        ? state.concepts.items[item.id].alt || item.title + ' painted concept'
        : board.alt || board.title,
    });
  if (item.assembly) {
    media.push(
      {
        key: 'assembly-plate',
        title: 'Assembly plate',
        file: './' + item.assembly.plate,
        alt: 'Exploded construction of ' + item.title,
      },
      {
        key: 'assembly-film',
        title: 'Assembly film',
        file: './' + item.assembly.clip,
        alt: 'Blender assembly sequence for ' + item.title,
      },
    );
  }
  return media;
}
function changeMedium(item, medium, choices) {
  state.medium = medium.key;
  byId('media-options').replaceChildren(
    ...choices.map((choice) => {
      const button = make('button', choice.title);
      button.type = 'button';
      button.setAttribute('aria-pressed', String(choice.key === medium.key));
      button.addEventListener('click', () => {
        changeMedium(item, choice, choices);
        byId('media-options').querySelector('[aria-pressed=true]')?.focus();
      });
      return button;
    }),
  );
  const previous = byId('media-view').querySelector('video');
  if (previous) {
    previous.pause();
    previous.removeAttribute('src');
    previous.load();
  }
  const figure = make('figure');
  if (medium.key === 'clip' || medium.key === 'assembly-film') {
    const video = make('video');
    video.controls = true;
    video.playsInline = true;
    video.preload = 'metadata';
    video.poster = './' + (medium.key === 'assembly-film' ? item.assembly.plate : item.render);
    video.src = medium.file;
    video.setAttribute('aria-label', medium.alt);
    figure.append(video);
  } else {
    const image = img(medium.file, medium.alt);
    image.loading = 'eager';
    figure.append(image);
  }
  const caption = make('figcaption');
  caption.append(make('span', medium.alt), link('Open file', medium.file));
  if (medium.key === 'concept' && conceptFile(item.id)) {
    const board = boardFor(item.id);
    if (board) caption.append(link('Original board', './concepts/' + board.file));
  }
  if (medium.key.startsWith('assembly-'))
    caption.append(link('Parts and timings', './' + item.assembly.parts));
  figure.append(caption);
  byId('media-view').replaceChildren(figure);
}
const svgNS = 'http://www.w3.org/2000/svg';
function svg(tag, attrs) {
  const node = document.createElementNS(svgNS, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  return node;
}
function locate(item) {
  const host = byId('locator');
  host.replaceChildren();
  const [west, south, east, north] = state.catalog.bounds;
  const map = svg('svg', {
    viewBox: [west - 4, -north - 4, east - west + 8, north - south + 8].join(' '),
    role: 'img',
    'aria-label': item.title + ' in the district floor plan',
  });
  for (const e of state.catalog.elements) {
    const active = e.id === item.id;
    if (e.kind === 'route' && e.travel_kind !== 'fold' && e.points_xyz?.length) {
      map.append(
        svg('polyline', {
          points: e.points_xyz.map(([x, y]) => x + ',' + -y).join(' '),
          fill: 'none',
          stroke: active ? '#a54527' : '#b4b5a8',
          'stroke-width': active ? 3 : 1,
        }),
      );
    }
  }
  for (const e of state.catalog.elements.filter((e) => e.kind === 'room')) {
    const [x, y] = e.center_xyz,
      [w, h] = e.size_m;
    map.append(
      svg('rect', {
        x: x - w / 2,
        y: -y - h / 2,
        width: w,
        height: h,
        fill: e.id === item.id ? '#e4a77b' : '#d9d7c9',
        stroke: '#73776c',
        'stroke-width': 0.8,
      }),
    );
  }
  const dotted = item.travel_kind === 'fold' && item.mouths_xyz?.length ? item.mouths_xyz : [item.center_xyz];
  for (const [x, y] of dotted)
    map.append(svg('circle', { cx: x, cy: -y, r: 3, fill: '#a23824', stroke: '#fff8e9', 'stroke-width': 1 }));
  const words = make('div');
  words.append(make('strong', item.title), make('p', item.cue || ''));
  if (item.travel_kind === 'fold') words.append(make('p', 'Both marks locate the paired fold mouths.'));
  else {
    const [x, y, z] = item.center_xyz;
    words.append(
      make(
        'p',
        'E ' +
          Number(x.toFixed(1)) +
          ' m · N ' +
          Number(y.toFixed(1)) +
          ' m · elevation ' +
          Number(z.toFixed(1)) +
          ' m',
      ),
    );
  }
  host.append(map, words);
}
function selectedList(item) {
  return state.matches.includes(item) ? state.matches : state.catalog.elements;
}
function updateDetail(item) {
  const changing = state.selected?.id !== item.id;
  state.selected = item;
  byId('detail-kind').textContent = kindNames[item.kind] || item.kind;
  byId('detail-title').textContent = item.title;
  byId('detail-brief').textContent = item.art_brief || '';
  const model = byId('element-model');
  model.href = './models/' + item.id + '.glb';
  model.textContent = 'Download ' + item.title + ' model (.glb) ↓';
  byId('permalink').href = '#element=' + encodeURIComponent(item.id);
  const list = selectedList(item);
  byId('position').textContent = list.indexOf(item) + 1 + ' / ' + list.length;
  const media = mediaFor(item);
  const wanted = changing ? (conceptFile(item.id) ? 'concept' : 'render') : state.medium;
  changeMedium(item, media.find((m) => m.key === wanted) || media[0], media);
  locate(item);
  const refs = item.source_refs || [];
  byId('sources').hidden = refs.length === 0;
  byId('item-sources').replaceChildren(
    ...refs.map((ref) => {
      const row = make('li');
      const u = new URL(
        ref.href,
        'https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-hanuman-trial/games/yuga-native/art/mandala-map-studio/',
      );
      if (u.protocol === 'https:' && !u.username && !u.password) row.append(link(ref.title, u.href));
      else row.textContent = ref.title;
      return row;
    }),
  );
  if (!dialog.open) dialog.showModal();
  if (changing) {
    dialog.scrollTop = 0;
    byId('location').open = false;
    byId('sources').open = false;
  }
}
function readLocation() {
  if (!state.catalog) return;
  const id = new URLSearchParams(location.hash.slice(1)).get('element');
  const item = id ? state.catalog.elements.find((e) => e.id === id) : null;
  if (item) {
    if (state.selected?.id !== id || !dialog.open) updateDetail(item);
    return;
  }
  if (dialog.open) {
    dialog.querySelector('video')?.pause();
    dialog.close();
    state.selected = null;
    (state.opener?.isConnected ? state.opener : byId('search')).focus({ preventScroll: true });
  }
}
function navigateTo(id) {
  const href = '#element=' + encodeURIComponent(id);
  if (dialog.open) history.replaceState(history.state, '', href);
  else history.pushState({ artStudy: true }, '', href);
  readLocation();
}
function dismiss() {
  if (history.state?.artStudy) history.back();
  else {
    history.replaceState(null, '', '#studies');
    readLocation();
    byId('studies').scrollIntoView();
  }
}
function move(delta) {
  if (!state.selected) return;
  const list = selectedList(state.selected),
    n = list.length;
  navigateTo(list[(list.indexOf(state.selected) + delta + n) % n].id);
}
byId('search').addEventListener('input', (event) => {
  state.search = event.target.value.trim();
  state.limit = pageSize;
  if (state.catalog) renderIndex();
});
byId('more').addEventListener('click', () => {
  const count = state.limit;
  state.limit += pageSize;
  renderIndex();
  byId('library').children[count]?.focus({ preventScroll: true });
});
byId('close').addEventListener('click', dismiss);
dialog.addEventListener('cancel', (event) => {
  event.preventDefault();
  dismiss();
});
dialog.addEventListener('keydown', (event) => {
  if (event.target.closest('video') || event.ctrlKey || event.altKey || event.metaKey || event.shiftKey)
    return;
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    event.preventDefault();
    move(event.key === 'ArrowLeft' ? -1 : 1);
  }
});
byId('previous').addEventListener('click', () => move(-1));
byId('next').addEventListener('click', () => move(1));
window.addEventListener('hashchange', readLocation);
window.addEventListener('popstate', readLocation);
const [catalog, concepts] = await Promise.allSettled([
  loadJSON('./catalog.json'),
  loadJSON('./concepts/index.json'),
]);
if (concepts.status === 'fulfilled') state.concepts = concepts.value;
renderBoards();
if (catalog.status === 'fulfilled' && Array.isArray(catalog.value?.elements)) {
  state.catalog = catalog.value;
  filters();
  renderIndex();
  readLocation();
} else {
  byId('index-count').textContent = 'The element catalog could not be loaded. Reload to try again.';
  byId('library').setAttribute('aria-busy', 'false');
  byId('search').disabled = true;
}
