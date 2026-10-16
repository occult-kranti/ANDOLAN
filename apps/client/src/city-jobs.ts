import { CONTRACTS, PROJECT_MILESTONES, getProjectLevel, getEffectiveJobReward, CITY_EXPOSE_JOB_ID, CITY_SECTORS, CITY_ROUTES, CITY_MEDIA_CARDS, type JobDefinition } from '../../../packages/content/src/contracts';
import { landmark } from '../../../packages/sim/src/world';
import type { Snapshot, CommandAction, CityRoute } from '../../../packages/protocol/src/index';

const $ = <T extends HTMLElement = HTMLElement>(selector: string) => document.querySelector<T>(selector)!;
const element = (tag: string, text: string, className = '') => {
  const node = document.createElement(tag); node.textContent = text; node.className = className; return node;
};
export const secondsLeft = (seconds: number) => {
  const value = Math.max(0, Math.ceil(seconds));
  return `${Math.floor(value / 60)}:${String(value % 60).padStart(2, '0')}`;
};
const orderedJobs = [...CONTRACTS].sort((a, b) => {
  const order = (job: JobDefinition) => job.id === CITY_EXPOSE_JOB_ID ? 0 : job.sector ? 1 : 2;
  return order(a) - order(b);
});

/** Job briefing uses authored requirements; the simulation owns eligibility and every reward. */
export class CityJobs {
  private selected = CITY_EXPOSE_JOB_ID;
  private signature = '';
  private ledgerSignature = '';
  private tab: 'jobs' | 'ledger' = 'jobs';
  private pending?: { kind: 'job'; jobId: string } | { kind: 'vote'; route: CityRoute };
  private pendingTimer = 0;
  private pendingRevision = -1;
  private state?: Snapshot;
  private local = true;
  private connected = false;
  private playerId = '';
  constructor(private readonly actions: {
    command: (action: CommandAction, target?: string, value?: string) => void;
    open: () => void;
    closeAndFocus?: () => void;
  }) {
    const tabs = element('nav', '', 'city-board-tabs'); tabs.setAttribute('aria-label', 'Dispatch sections');
    for (const [id, label] of [['jobs', 'Jobs'], ['ledger', 'City ledger']] as const) {
      const button = document.createElement('button'); button.id = `city-tab-${id}`; button.textContent = label;
      button.addEventListener('click', () => { this.tab = id; this.render(); }); tabs.append(button);
    }
    const feedback = element('p', '', 'job-request-status'); feedback.id = 'job-request-status'; feedback.setAttribute('role', 'status');
    $('#jobs-summary').after(tabs, feedback);
    const selector = element('div', '', 'job-select-wrap');
    const label = document.createElement('label'); label.htmlFor = 'job-select'; label.textContent = 'Choose a job';
    const select = document.createElement('select'); select.id = 'job-select';
    select.addEventListener('change', () => { this.selected = select.value; this.signature = ''; this.render(); });
    selector.append(label, select); $('.jobs-layout').before(selector);
    const ledger = element('section', '', 'city-ledger'); ledger.id = 'city-ledger'; ledger.setAttribute('aria-label', 'City evidence, sectors and mandate'); $('.jobs-layout').after(ledger);
    for (const [index, job] of orderedJobs.entries()) {
      const option = document.createElement('option'); option.value = job.id; option.textContent = job.title; select.append(option);
      const button = document.createElement('button'); button.className = 'job-option'; button.dataset.jobId = job.id;
      const number = element('span', String(index + 1).padStart(2, '0'), 'job-number');
      const label = element('span', '', 'job-label');
      label.append(element('strong', job.title), element('small', job.kind, 'job-availability'));
      button.append(number, label);
      button.addEventListener('click', () => { this.selected = job.id; this.signature = ''; this.render(); });
      $('#job-list').append(button);
    }
  }
  show() {
    if (this.state?.contracts?.active) this.selected = this.state.contracts.active.jobId;
    this.tab = 'jobs';
    this.signature = ''; this.render(); this.actions.open();
  }
  showLedger() { this.tab = 'ledger'; this.render(); this.actions.open(); }
  /** Rejections never close the briefing or imply authoritative success. */
  clearPending(message = 'The request was not completed. You can try again.') {
    if (!this.pending) return;
    this.pending = undefined; window.clearTimeout(this.pendingTimer); this.pendingTimer = 0;
    $('#job-request-status').textContent = message;
    this.render();
  }
  private request(pending: NonNullable<CityJobs['pending']>, action: CommandAction, target: string, value?: string) {
    if (this.pending || !this.connected) return;
    this.pending = pending;
    this.pendingRevision = this.state?.city.revision ?? -1;
    $('#job-request-status').textContent = pending.kind === 'job' ? 'Waiting for the city to accept this job…' : 'Sending your mandate vote…';
    this.pendingTimer = window.setTimeout(() => this.clearPending('No response yet. Check your connection, then try again.'), 6000);
    this.render();
    this.actions.command(action, target, value);
  }
  update(state: Snapshot, playerId: string, local: boolean, connected: boolean) {
    this.state = state; this.playerId = playerId; this.local = local; this.connected = connected;
    const pending = this.pending;
    if (pending) {
      if (!connected) this.clearPending('Connection paused. Your job has not been confirmed.');
      else if (pending.kind === 'job' && state.contracts.active) {
        const accepted = state.contracts.active.jobId === pending.jobId;
        this.clearPending(accepted ? 'Job accepted. Follow the marked objective.' : 'Your crew accepted another job. Review the shared objective.');
        if (accepted && $<HTMLDialogElement>('#jobs-dialog').open) {
          if (this.actions.closeAndFocus) this.actions.closeAndFocus(); else $<HTMLDialogElement>('#jobs-dialog').close();
        }
      } else if (pending.kind === 'vote' && (state.city.decision || state.city.revision > this.pendingRevision && state.city.votes[playerId] === pending.route)) this.clearPending('Your mandate vote is recorded.');
    }
    if ($<HTMLDialogElement>('#jobs-dialog').open) this.render();
  }
  private unavailable(job: JobDefinition): string {
    const state = this.state!;
    if (job.once && state.city.completedJobs.includes(job.id)) return 'CASE COMPLETE';
    if (job.requiresJobs?.some(id => !state.city.completedJobs.includes(id))) return 'FIRST: THE NINE O’CLOCK CORRECTION';
    if (state.contracts.progression.reputation < (job.minReputation || 0)) return `UNLOCKS AT ${job.minReputation} REPUTATION`;
    return '';
  }
  private render() {
    const state = this.state, contracts = state?.contracts;
    if (!state || !contracts) return;
    const { progression, active } = contracts;
    const job = CONTRACTS.find(item => item.id === this.selected) || CONTRACTS[0];
    const isActive = active?.jobId === job.id;
    const cooldown = Math.max(0, (contracts.cooldowns[job.id] || 0) - state.time);
    const unavailable = this.unavailable(job);
    $('#city-tab-jobs').setAttribute('aria-pressed', String(this.tab === 'jobs'));
    $('#city-tab-ledger').setAttribute('aria-pressed', String(this.tab === 'ledger'));
    $('.jobs-layout').classList.toggle('hidden', this.tab !== 'jobs');
    $('.job-select-wrap').classList.toggle('hidden', this.tab !== 'jobs');
    $('#city-ledger').classList.toggle('hidden', this.tab !== 'ledger');
    $<HTMLSelectElement>('#job-select').value = job.id;
    $('#jobs-summary').textContent = `${progression.credits.toLocaleString()} crew credits / ${progression.reputation} reputation / ${progression.completed} jobs completed`;
    $('#jobs-scope').textContent = this.local ? 'Solo practice · saved on this device' : 'Shared room progress · server saved';
    for (const button of document.querySelectorAll<HTMLButtonElement>('[data-job-id]')) {
      const item = CONTRACTS.find(value => value.id === button.dataset.jobId)!;
      const waiting = Math.max(0, (contracts.cooldowns[item.id] || 0) - state.time);
      button.setAttribute('aria-pressed', String(item.id === job.id));
      const availability = active?.jobId === item.id ? 'IN PROGRESS' : this.unavailable(item) || (waiting ? `BACK IN ${secondsLeft(waiting)}` : `${item.kind.toUpperCase()} / ${getEffectiveJobReward(item.reward, state.city.decision?.route ?? null).credits} CREDITS`);
      button.querySelector('.job-availability')!.textContent = availability;
      const option = [...$<HTMLSelectElement>('#job-select').options].find(value => value.value === item.id);
      if (option) option.textContent = `${item.title} — ${availability}`;
    }
    const signature = JSON.stringify([job.id, active?.instanceId, active?.stageIndex, active?.orphanedAt, active?.participants, progression, state.city.revision, this.connected, this.playerId]);
    if (signature !== this.signature) {
      this.signature = signature;
      const detail = $('#job-detail');
      const focused = detail.contains(document.activeElement) ? (document.activeElement as HTMLElement).id : '';
      const tipsExpanded = detail.dataset.selectedJob === job.id && !!detail.querySelector<HTMLDetailsElement>('.job-role-tips')?.open;
      detail.dataset.selectedJob = job.id; detail.replaceChildren();
      const title = element('h3', job.title, 'job-title'); title.id = 'job-detail-title'; title.tabIndex = -1;
      detail.append(element('p', `${job.kind} / ${job.stages.length} steps`, 'eyebrow'), title, element('p', job.description, 'job-description'));
      const rewards = element('div', '', 'job-rewards');
      const reward = getEffectiveJobReward(job.reward, state.city.decision?.route ?? null);
      for (const text of [`+${reward.credits} crew credits`, `+${reward.reputation} reputation`, `${reward.project} project ${reward.project === 1 ? 'point' : 'points'}`]) rewards.append(element('span', text));
      detail.append(rewards);
      if (state.city.decision) detail.append(element('p', `Rewards follow this city’s permanent mandate: ${CITY_ROUTES[state.city.decision.route].label}.`, 'job-project-note'));
      if (job.once) detail.append(element('p', 'One-time case · completion stays in this city’s ledger.', 'job-project-note'));
      if (job.timeLimitSeconds) detail.append(element('p', `Time limit: ${secondsLeft(job.timeLimitSeconds)} from acceptance. Get your car ready first.`, 'job-time-limit'));
      const route = element('ol', '', 'job-route');
      for (const [index, stage] of job.stages.entries()) {
        const row = element('li', '', isActive && index < active.stageIndex ? 'complete' : isActive && index === active.stageIndex ? 'current' : '');
        row.append(element('strong', stage.targetVehicleId ? 'Locate the actual vehicle' : landmark(stage.targetId)?.name || stage.targetId), element('span', stage.objective));
        route.append(row);
      }
      detail.append(route);
      if (job.crewTips?.length) {
        const tips = document.createElement('details'); tips.className = 'job-role-tips';
        tips.open = tipsExpanded;
        const summary = element('summary', 'How your crew can help'); summary.id = 'job-role-tips-toggle'; tips.append(summary);
        for (const tip of job.crewTips) tips.append(element('p', `${tip.role[0].toUpperCase()}${tip.role.slice(1)} — ${tip.text}`));
        detail.append(tips);
      }
      if (isActive) {
        const status = element('p', active.objective, 'job-active-note'); status.id = 'job-active-note'; detail.append(status);
        const timer = element('p', '', 'job-time-limit'); timer.id = 'job-timer'; detail.append(timer);
        const cancel = document.createElement('button'); cancel.id = 'job-cancel'; cancel.className = 'button quiet'; cancel.textContent = 'Abandon this job';
        const owner = state.players.find(player => player.id === active.startedBy);
        const canCancel = active.startedBy === this.playerId || (!owner?.connected && (active.participants.includes(this.playerId) || (active.orphanedAt !== null && state.time - active.orphanedAt >= 30)));
        cancel.disabled = !this.connected || !canCancel;
        cancel.addEventListener('click', () => {
          if (window.confirm('Abandon this crew job? No rewards will be earned.')) this.actions.command('job_cancel', active.instanceId);
        });
        detail.append(cancel);
      } else {
        const start = document.createElement('button'); start.id = 'job-start'; start.className = 'button primary';
        start.addEventListener('click', () => this.request({ kind: 'job', jobId: job.id }, 'job_start', job.id)); detail.append(start);
      }
      const milestone = PROJECT_MILESTONES[getProjectLevel(progression.project)];
      detail.append(element('p', `${milestone.title} · ${progression.project} project points. ${milestone.description}`, 'job-project-note'));
      if (focused) {
        const target = document.getElementById(focused);
        (target && detail.contains(target) && !target.matches(':disabled') ? target : title).focus({ preventScroll: true });
      }
    }
    const start = document.querySelector<HTMLButtonElement>('#job-start');
    if (start) {
      start.disabled = !this.connected || !!this.pending || !!active || !!unavailable || cooldown > 0;
      start.textContent = !this.connected ? 'Waiting for connection' : this.pending ? 'Waiting for confirmation…' : active ? 'Finish or abandon the current job first' : unavailable || (cooldown > 0 ? `Available in ${secondsLeft(cooldown)}` : 'Accept job for the crew');
    }
    const timer = document.querySelector('#job-timer');
    if (timer && active) timer.textContent = active.deadlineAt === null ? 'No time limit. Finish at your crew’s pace.' : `Time remaining: ${secondsLeft(active.deadlineAt - state.time)}`;
    const cancel = document.querySelector<HTMLButtonElement>('#job-cancel');
    if (cancel && active) {
      const owner = state.players.find(player => player.id === active.startedBy);
      const canRecover = !owner?.connected && (active.participants.includes(this.playerId) || (active.orphanedAt !== null && state.time - active.orphanedAt >= 30));
      cancel.disabled = !this.connected || !(active.startedBy === this.playerId || canRecover);
    }
    this.renderLedger();
  }

  private renderLedger() {
    const state = this.state!; const { city, contracts: { active } } = state;
    const completed = new Set(city.completedJobs);
    const sectors = CITY_SECTORS.filter(sector => city.sectors[sector.id] >= 1).length;
    const requiredCases = CONTRACTS.filter(job => job.id === CITY_EXPOSE_JOB_ID || job.sector);
    const ready = requiredCases.every(job => completed.has(job.id)) && sectors === CITY_SECTORS.length;
    const ledger = $('#city-ledger');
    $('#city-tab-ledger').textContent = city.decision ? 'City ledger · mandate recorded' : ready ? 'City ledger · choose mandate' : `City ledger · ${sectors}/${CITY_SECTORS.length} sectors`;
    const signature = JSON.stringify([city, active?.instanceId, active?.stageIndex]);
    if (signature !== this.ledgerSignature) {
      this.ledgerSignature = signature;
      const focused = ledger.contains(document.activeElement) ? (document.activeElement as HTMLElement).id : '';
      const receiptsExpanded = ledger.querySelector<HTMLDetailsElement>('.city-receipts')?.open ?? false;
      ledger.replaceChildren(element('p', 'Authored city fiction · no live news or real-world trend data', 'eyebrow'), element('h3', 'The record behind the broadcast', 'job-title'));
      ledger.append(element('p', 'Start with The Nine O’Clock Correction. Complete the four sector cases, then bring the full record to Public Hearing. Your crew decides what the next administration inherits.', 'job-description'));
      const grid = element('div', '', 'city-sector-grid');
      for (const sector of CITY_SECTORS) {
        const card = element('article', '', 'city-sector');
        card.append(element('h4', sector.label), element('p', city.sectors[sector.id] >= 1 ? 'Case completed · evidence recorded' : completed.has(CITY_EXPOSE_JOB_ID) ? 'Case available on the job board' : 'Opens after The Nine O’Clock Correction', 'city-sector-state'), element('p', sector.description));
        grid.append(card);
      }
      ledger.append(grid);
      const mandate = element('section', '', 'city-mandate'); mandate.setAttribute('aria-labelledby', 'city-mandate-heading');
      const heading = element('h3', city.outcome?.title || 'Who inherits the city?'); heading.id = 'city-mandate-heading'; heading.tabIndex = -1;
      mandate.append(heading);
      if (city.outcome && city.decision) {
        mandate.append(element('p', city.outcome.description), element('p', CITY_ROUTES[city.decision.route].consequence, 'city-consequence'));
      } else {
        const status = element('p', '', 'city-ledger-status'); status.id = 'city-mandate-status'; status.setAttribute('role', 'status'); mandate.append(status);
        if (ready) mandate.append(element('p', 'Choose at Public Hearing, on foot. The connected crew must reach a majority. You may change your ballot until a decision is recorded; the outcome is permanent for this city save.', 'city-vote-help'));
        for (const route of ready ? ['reform', 'capture'] as const : []) {
          const choice = CITY_ROUTES[route];
          const button = document.createElement('button'); button.id = `city-route-${route}`; button.className = 'city-route-button';
          button.append(element('strong', choice.label), element('span', choice.description), element('span', choice.consequence, 'city-consequence'), element('small', '', 'city-vote-count'));
          button.addEventListener('click', () => this.request({ kind: 'vote', route }, 'city_choice', 'city-mandate', route));
          mandate.append(button);
        }
      }
      ledger.append(mandate);
      const media = element('section', '', 'city-media'); media.setAttribute('aria-label', 'Fictional press dispatches');
      media.append(element('h3', 'Fictional press dispatches'));
      for (const card of CITY_MEDIA_CARDS.filter(item => !item.requiresJobs?.some(id => !completed.has(id)))) {
        const article = element('article', '', 'city-media-card'); article.dataset.mediaId = card.id;
        article.append(element('p', `${card.outlet} / ${card.speaker}`, 'eyebrow'), element('h4', card.title), element('p', card.body)); media.append(article);
      }
      ledger.append(media);
      const receipts = CONTRACTS.flatMap(job => job.stages.flatMap((stage, index) => stage.event && (completed.has(job.id) || active?.jobId === job.id && index < active.stageIndex) ? [{ job, stage }] : []));
      if (receipts.length) {
        const details = document.createElement('details'); details.className = 'city-receipts';
        details.open = receiptsExpanded;
        const summary = element('summary', `Read earned case receipts (${receipts.length})`); summary.id = 'city-receipts-toggle'; details.append(summary);
        for (const { job, stage } of receipts) {
          const receipt = element('article', '', 'city-media-card'); receipt.dataset.receipt = `${job.id}:${stage.id}`;
          receipt.append(element('h4', stage.event!.title), element('p', stage.event!.body)); details.append(receipt);
        }
        ledger.append(details);
      }
      if (focused) (document.getElementById(focused) || heading).focus({ preventScroll: true });
    }
    if (city.decision) return;
    const player = state.players.find(item => item.id === this.playerId);
    const hall = landmark('civic')!;
    const nearby = !!player && Math.hypot(player.x - hall.x, player.z - hall.z) <= hall.radius;
    const crew = state.players.filter(item => item.connected);
    const threshold = Math.floor(crew.length / 2) + 1;
    const votes = crew.map(item => city.votes[item.id]);
    const reason = !this.connected ? 'Reconnect to cast a vote.' : !ready ? `Casework: ${requiredCases.filter(job => completed.has(job.id)).length}/${requiredCases.length} complete. Finish the correction and all four sector cases.` : active ? 'Finish or abandon the active job before the mandate.' : player?.vehicleId ? 'Exit your vehicle at Public Hearing to vote.' : !nearby ? 'Travel to Public Hearing to cast your vote.' : 'Ready to vote at Public Hearing.';
    const status = $('#city-mandate-status');
    const text = `${reason} ${threshold} matching ${threshold === 1 ? 'vote' : 'votes'} needed from ${crew.length} connected crew. A tie waits. A departure alone never finalizes the decision; cast a fresh vote.`;
    if (status.textContent !== text) status.textContent = text;
    if (!ready) return;
    for (const route of ['reform', 'capture'] as const) {
      const button = $<HTMLButtonElement>(`#city-route-${route}`);
      button.disabled = !this.connected || !ready || !!active || !!player?.vehicleId || !nearby || !!this.pending;
      button.setAttribute('aria-pressed', String(city.votes[this.playerId] === route));
      const count = votes.filter(vote => vote === route).length;
      button.querySelector('.city-vote-count')!.textContent = `${count}/${threshold} matching${city.votes[this.playerId] === route ? ' · your current vote' : ''}${this.pending?.kind === 'vote' && this.pending.route === route ? ' · sending…' : ''}`;
    }
  }
}
