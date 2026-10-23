const byId = (id) => document.getElementById(id);
const state = {data: null, paused: false, loading: false, selectedId: null, mode: 'connecting', lastJobs: '', lastDetail: '', lastAssets: '', lastMilestones: '', lastSources: '', failure: ''};
const statusNames = {queued: 'Queued', running: 'Running', review: 'In review', complete: 'Complete', blocked: 'Blocked', failed: 'Failed', stale: 'Stale'};
const statusOrder = {running: 0, review: 1, blocked: 2, failed: 3, stale: 4, queued: 5, complete: 6};
const text = (value, fallback = 'Not recorded') => (typeof value === 'string' || typeof value === 'number') && String(value).trim() ? String(value) : fallback;
const array = (value) => Array.isArray(value) ? value : [];
const set = (id, value) => { byId(id).textContent = value; };
const element = (tag, className, value) => { const node = document.createElement(tag); if (className) node.className = className; if (value !== undefined) node.textContent = value; return node; };
const timestamp = (value) => { const n = Date.parse(value); return Number.isFinite(n) ? n : null; };
const date = (value) => { const n = timestamp(value); return n === null ? 'Not recorded' : new Date(n).toLocaleString(undefined, {dateStyle: 'medium', timeStyle: 'short'}); };
const age = (value) => { const n = timestamp(value); if (n === null) return 'Age unavailable'; const s = Math.max(0, Math.floor((Date.now() - n) / 1000)); if (s < 60) return `${s}s ago`; if (s < 3600) return `${Math.floor(s / 60)}m ago`; if (s < 86400) return `${Math.floor(s / 3600)}h ago`; return `${Math.floor(s / 86400)}d ago`; };
const bytes = (value) => Number.isFinite(value) && value >= 0 ? `${(value / (1024 ** 3)).toFixed(1)} GiB` : null;
function safeUrl(value) {
  if (typeof value !== 'string' || !value || /[\u0000-\u0020\u007f\\]/.test(value)) return null;
  try {
    const parsed = new URL(value, document.baseURI);
    if (parsed.username || parsed.password) return null;
    if (parsed.protocol === 'https:' || (parsed.origin === location.origin && ['http:', 'https:'].includes(parsed.protocol))) return parsed.href;
  } catch { /* Invalid links are rendered as plain text. */ }
  return null;
}
function link(label, value, className) {
  const href = safeUrl(value);
  if (!href) return element('span', className, label);
  const node = element('a', className, label);
  node.href = href;
  if (new URL(href).origin !== location.origin) { node.target = '_blank'; node.rel = 'noopener noreferrer'; }
  return node;
}
function modelName(value) {
  if (value && typeof value === 'object') return text(value.name ?? value.id ?? value.model, 'No model recorded');
  return text(value, 'No model recorded');
}
function statusNode(value) {
  const status = Object.hasOwn(statusNames, value) ? value : 'queued';
  let label = statusNames[status];
  if (status === 'running' && (state.mode !== 'live' || state.paused)) label = 'Recorded running';
  const node = element('span', 'status-label', label);
  node.dataset.status = status;
  return node;
}
function field(label, value, timeValue) {
  const row = element('div');
  row.append(element('dt', '', label));
  const dd = element('dd');
  if (timeValue && timestamp(timeValue) !== null) { const time = element('time', '', value); time.dateTime = new Date(timestamp(timeValue)).toISOString(); dd.append(time); }
  else dd.textContent = value;
  row.append(dd);
  return row;
}
function currentMode() {
  if (!state.data) return 'connecting';
  if (state.data.mode !== 'live') return 'snapshot';
  const recorded = timestamp(state.data.collected_at);
  if (recorded === null || Date.now() - recorded > 15000 || recorded - Date.now() > 30000) return 'stale';
  return 'live';
}
function renderConnection() {
  state.mode = currentMode();
  const band = document.querySelector('.connection-band');
  band.dataset.mode = state.mode;
  const labels = {connecting: 'Connecting to build worker', live: 'Live worker observation', snapshot: 'Saved snapshot — not live', stale: 'Stale worker observation — not live'};
  set('connection-label', state.paused ? 'Updates paused — showing last observation' : labels[state.mode]);
  set('connection-age', state.data ? `Observed ${age(state.data.collected_at)} · ${date(state.data.collected_at)}` : 'Waiting for the first observation');
  const notes = {connecting: 'Checking this worker for live telemetry. A saved export will be clearly marked.', live: 'Machine availability is observed here. Public GPU services and unconnected personal devices have separate job records.', snapshot: 'The live worker is unavailable. Jobs and machine values below are historical records from this export, not current activity.', stale: 'The worker timestamp is old or missing. Refresh to request a new observation; recorded running jobs are not confirmed active.'};
  set('connection-note', state.paused ? 'Automatic requests are paused. Refresh now obtains one observation without resuming automatic updates.' : notes[state.mode]);
  set('pause-button', state.paused ? 'Resume updates' : 'Pause updates');
  byId('pause-button').setAttribute('aria-pressed', String(state.paused));
  if (state.data) set('footer-time', `Data recorded ${date(state.data.collected_at)}`);
}
function renderHost() {
  const host = state.data.host ?? {};
  const cpu = Number.isFinite(host.quota_cpus) ? `${host.quota_cpus} CPU quota` : Number.isFinite(host.logical_cpus) ? `${host.logical_cpus} logical CPUs` : 'Not reported';
  set('cpu-observation', cpu);
  const total = bytes(host.memory_total_bytes), available = bytes(host.memory_available_bytes);
  set('memory-observation', total ? (available ? `${available} available / ${total}` : `${total} total`) : 'Not reported');
  const gpu = host.gpu ?? {};
  const devices = array(gpu.devices);
  set('gpu-observation', gpu.available === true ? devices.map((d) => text(d.name, 'Unnamed device')).join(', ') || 'Device reported' : gpu.available === false ? 'No attached GPU observed' : 'Not reported');
  set('gpu-note', text(gpu.reason, 'Public GPU jobs are recorded individually; they do not imply an attached GPU.'));
}
function renderDeviceOptions() {
  const select = byId('device-filter');
  const values = [...new Set(array(state.data.jobs).map((job) => text(job.device, 'Unspecified')))];
  const existing = [...select.options].slice(1).map((option) => option.value);
  if (JSON.stringify(existing) === JSON.stringify(values)) return;
  const selected = select.value;
  select.replaceChildren(new Option('All compute', 'all'), ...values.map((value) => new Option(value, value)));
  select.value = values.includes(selected) ? selected : 'all';
}
function renderJobs(force = false) {
  const jobs = array(state.data.jobs);
  const selectedStatus = byId('status-filter').value;
  const selectedDevice = byId('device-filter').value;
  const visible = jobs.filter((job) => (selectedStatus === 'all' || job.status === selectedStatus) && (selectedDevice === 'all' || text(job.device, 'Unspecified') === selectedDevice)).sort((a, b) => (statusOrder[a.status] ?? 9) - (statusOrder[b.status] ?? 9));
  if (!visible.some((job) => job.id === state.selectedId)) state.selectedId = visible[0]?.id ?? null;
  const signature = JSON.stringify([visible, state.mode, state.paused, state.selectedId]);
  const running = jobs.filter((job) => job.status === 'running').length;
  const review = jobs.filter((job) => job.status === 'review').length;
  const runLabel = state.mode === 'live' && !state.paused ? 'running' : 'recorded as running';
  set('queue-summary', `${jobs.length} recorded jobs · ${running} ${runLabel} · ${review} awaiting review`);
  byId('empty-queue').hidden = visible.length > 0;
  if (!force && signature === state.lastJobs) return;
  state.lastJobs = signature;
  const activeId = document.activeElement?.dataset?.jobId;
  const list = byId('job-list');
  list.replaceChildren();
  for (const job of visible) {
    const row = element('button', 'job-row');
    row.type = 'button';
    row.dataset.jobId = text(job.id, 'unknown');
    row.setAttribute('aria-pressed', String(job.id === state.selectedId));
    row.setAttribute('aria-controls', 'job-detail');
    const copy = element('span');
    copy.append(element('span', 'job-row-title', text(job.title, 'Untitled job')), element('span', 'job-row-meta', `${text(job.owner, 'Unassigned')} · ${text(job.stage, 'No stage')} · ${age(job.updated_at)}`));
    row.append(copy, element('span', 'job-device', text(job.device, 'Unspecified')), statusNode(job.status));
    row.addEventListener('click', () => { state.selectedId = job.id; state.lastDetail = ''; renderJobs(true); renderDetail(); byId('announcer').textContent = `${text(job.title)} details selected.`; });
    list.append(row);
  }
  if (activeId) [...list.children].find((node) => node.dataset.jobId === activeId)?.focus({preventScroll: true});
  for (const row of list.children) row.setAttribute('aria-pressed', String(row.dataset.jobId === String(state.selectedId)));
}
function renderDetail() {
  const job = array(state.data.jobs).find((item) => item.id === state.selectedId);
  const signature = JSON.stringify([job, state.mode, state.paused]);
  if (signature === state.lastDetail) return;
  state.lastDetail = signature;
  const detail = byId('job-detail');
  detail.replaceChildren();
  const stateElement = byId('inspector-status');
  if (!job) {
    set('inspector-title', 'No job selected');
    stateElement.replaceWith(Object.assign(statusNode('queued'), {id: 'inspector-status'}));
    detail.append(element('p', '', 'The next recorded job will include its model, observations, outputs and next action.'));
    return;
  }
  set('inspector-title', text(job.title, 'Untitled job'));
  stateElement.replaceWith(Object.assign(statusNode(job.status), {id: 'inspector-status'}));
  detail.append(element('p', '', text(job.summary, 'No summary recorded for this job.')));
  const metadata = element('dl');
  metadata.append(field('Owner', text(job.owner, 'Unassigned')), field('Compute', text(job.device, 'Unspecified')), field('Model / tool', modelName(job.model)), field('Stage', text(job.stage)), field('Started', date(job.started_at), job.started_at), field('Updated', date(job.updated_at), job.updated_at));
  if (job.finished_at) metadata.append(field('Finished', date(job.finished_at), job.finished_at));
  detail.append(metadata);
  if (array(job.outputs).length) {
    detail.append(element('h4', '', 'Recorded outputs'));
    const outputs = element('ul');
    for (const output of job.outputs) { const item = element('li'); item.append(link(text(output.label ?? output.path, 'Output'), output.url)); outputs.append(item); }
    detail.append(outputs);
  }
  const next = element('div', 'inspector-next');
  next.append(element('h4', '', 'Next step'), element('p', '', text(job.next_step, 'No next step recorded.')));
  detail.append(next);
}
function imageNode(url, label, className, placeholderText) {
  const src = safeUrl(url);
  if (!src) return element('div', 'artifact-image-placeholder', placeholderText);
  const img = element('img', className);
  img.src = src; img.alt = label; img.loading = 'lazy'; img.decoding = 'async';
  img.addEventListener('error', () => img.replaceWith(element('div', 'artifact-image-placeholder', 'The recorded preview could not be loaded. Open its source output instead.')), {once: true});
  return img;
}
function renderAssets() {
  const assets = array(state.data.assets);
  const signature = JSON.stringify(assets);
  if (signature === state.lastAssets) return;
  state.lastAssets = signature;
  const lead = assets.find((asset) => safeUrl(asset.image_url));
  const img = byId('lead-image');
  img.hidden = !lead;
  byId('lead-placeholder').hidden = Boolean(lead);
  if (lead) {
    img.src = safeUrl(lead.image_url); img.alt = `Recorded output: ${text(lead.title, 'YUGA asset')}`;
    img.onerror = () => { img.hidden = true; byId('lead-placeholder').hidden = false; set('lead-placeholder', 'This recorded preview could not be loaded.'); };
    set('lead-caption', text(lead.title, 'Recorded asset'));
    set('lead-status', text(lead.status, 'Review pending'));
  }
  byId('empty-artifacts').hidden = assets.length > 0;
  const list = byId('artifact-list');
  list.replaceChildren();
  for (const asset of assets) {
    const article = element('article', 'artifact');
    article.append(imageNode(asset.image_url, `Recorded output: ${text(asset.title, 'YUGA asset')}`, 'artifact-image', 'Preview not recorded yet.'));
    const heading = element('div', 'artifact-title');
    heading.append(element('h3', '', text(asset.title, 'Untitled artifact')));
    article.append(heading, element('span', 'status-label', text(asset.status, 'Review pending')), element('p', '', text(asset.summary, 'No inspection summary recorded.')));
    const links = element('div', 'artifact-links');
    if (safeUrl(asset.image_url)) links.append(link('Open render', asset.image_url));
    if (safeUrl(asset.model_url)) links.append(link('Open 3D source', asset.model_url));
    article.append(links);
    list.append(article);
  }
}
function renderMilestones() {
  const milestones = array(state.data.milestones);
  const signature = JSON.stringify([milestones, state.mode]);
  if (signature === state.lastMilestones) return;
  state.lastMilestones = signature;
  byId('empty-roadmap').hidden = milestones.length > 0;
  const list = byId('milestone-list');
  list.replaceChildren();
  for (const milestone of milestones) {
    const item = element('li', 'milestone');
    const marker = element('div');
    marker.append(element('div', 'milestone-id', text(milestone.id, 'Stage')), statusNode(milestone.status));
    const copy = element('div');
    copy.append(element('h3', '', text(milestone.title, 'Untitled stage')));
    const evidence = typeof milestone.evidence === 'string' ? milestone.evidence : Array.isArray(milestone.evidence) ? milestone.evidence.map((entry) => text(entry)).join(' · ') : 'Acceptance evidence is not recorded yet.';
    copy.append(element('p', '', evidence));
    item.append(marker, copy); list.append(item);
  }
}
function renderSources() {
  const sources = array(state.data.sources);
  const signature = JSON.stringify(sources);
  if (signature === state.lastSources) return;
  state.lastSources = signature;
  byId('empty-sources').hidden = sources.length > 0;
  document.querySelector('.source-table-wrap').hidden = sources.length === 0;
  const list = byId('source-list');
  list.replaceChildren();
  for (const source of sources) {
    const row = element('tr'), name = element('td');
    name.append(link(text(source.name, 'Unnamed resource'), source.url));
    row.append(name, element('td', '', text(source.license, 'Terms not recorded')), element('td', '', text(source.status)));
    list.append(row);
  }
}
function render() {
  const data = state.data;
  byId('error-panel').hidden = true;
  byId('dashboard').hidden = false;
  byId('dashboard').setAttribute('aria-busy', 'false');
  set('run-title', text(data.run?.title, 'The next piece of YUGA'));
  set('run-summary', text(data.run?.summary, 'Original game production, using existing tools and source assets. Inspect each job for its actual output and next acceptance step.'));
  set('source-commit', text(data.source?.commit, 'Not observed').slice(0, 12));
  set('source-branch', text(data.source?.branch, 'Branch not observed'));
  set('source-dirty', data.source?.dirty === true ? 'Local changes' : data.source?.dirty === false ? 'Clean checkout' : 'Working state not reported');
  renderConnection(); renderHost(); renderDeviceOptions(); renderJobs(); renderDetail(); renderAssets(); renderMilestones(); renderSources();
}
async function getJson(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 6000);
  try {
    const response = await fetch(url, {cache: 'no-store', credentials: 'same-origin', signal: controller.signal});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const record = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
    if (!record(data) || data.schema_version !== 1 || !Array.isArray(data.jobs) || !record(data.run) || !['live', 'snapshot'].includes(data.mode)) throw new Error('Unsupported observation format');
    if (data.jobs.some((job) => !record(job) || typeof job.id !== 'string' || !job.id.trim() || (job.outputs !== undefined && (!Array.isArray(job.outputs) || job.outputs.some((output) => !record(output)))))) throw new Error('Invalid job records');
    if (new Set(data.jobs.map((job) => job.id)).size !== data.jobs.length) throw new Error('Duplicate job identity');
    for (const key of ['assets', 'milestones', 'sources']) if (data[key] !== undefined && (!Array.isArray(data[key]) || data[key].some((row) => !record(row)))) throw new Error('Invalid observation records');
    for (const key of ['host', 'source']) if (data[key] !== undefined && !record(data[key])) throw new Error('Invalid observation context');
    return data;
  } finally { clearTimeout(timeout); }
}
async function refresh(manual = false) {
  if (state.loading || (state.paused && !manual)) return;
  state.loading = true;
  byId('refresh-button').disabled = true;
  try {
    try { state.data = await getJson('/api/status'); }
    catch { state.data = await getJson('./status.json'); state.data.mode = 'snapshot'; }
    state.failure = '';
    render();
    if (manual) set('announcer', `Observation refreshed. ${state.mode === 'live' ? 'Live worker connected.' : 'Showing a saved observation.'}`);
  } catch {
    state.failure = 'The live worker and saved export could not be read. Check the worker connection, then refresh.';
    if (state.data) { state.data.mode = 'snapshot'; renderConnection(); renderJobs(); renderDetail(); set('connection-note', 'Refresh failed. Preserved the last successful observation; current activity is not confirmed.'); }
    else { byId('error-panel').hidden = false; byId('dashboard').hidden = true; set('connection-label', 'No observation available'); set('connection-age', 'Connection failed'); set('connection-note', state.failure); set('error-message', state.failure); }
    if (manual) set('announcer', state.failure);
  } finally { state.loading = false; byId('refresh-button').disabled = false; }
}
function clearFilters() { byId('status-filter').value = 'all'; byId('device-filter').value = 'all'; if (state.data) { renderJobs(true); renderDetail(); } }
byId('status-filter').addEventListener('change', () => { if (state.data) { renderJobs(true); renderDetail(); } });
byId('device-filter').addEventListener('change', () => { if (state.data) { renderJobs(true); renderDetail(); } });
byId('clear-filters').addEventListener('click', clearFilters);
byId('empty-clear').addEventListener('click', clearFilters);
byId('refresh-button').addEventListener('click', () => refresh(true));
byId('retry-button').addEventListener('click', () => refresh(true));
byId('pause-button').addEventListener('click', () => {
  state.paused = !state.paused;
  renderConnection();
  if (state.data) { renderJobs(); renderDetail(); }
  set('announcer', state.paused ? 'Automatic updates paused.' : 'Automatic updates resumed.');
  if (!state.paused) refresh();
});
setInterval(() => refresh(), 3000);
setInterval(() => {
  const previous = state.mode;
  renderConnection();
  if (state.data && previous !== state.mode) { renderJobs(); renderDetail(); }
}, 1000);
refresh();
