import type { LandmarkId } from './index.js';

/** Original repeatable city work. Content declares requirements; the server owns progress and rewards. */
export const CONTRACTS_VERSION = '0.2.0';

export type JobKind = 'delivery' | 'recovery' | 'circuit' | 'civic';
export type JobVehicle = 'any' | 'car' | 'van' | 'none';
export type CityRoute = 'reform' | 'capture';
export type CitySector = 'energy' | 'welfare' | 'resources' | 'procurement';
export interface JobReward { credits: number; reputation: number; project: number }
export interface JobStage {
  id: string;
  objective: string;
  targetId: LandmarkId;
  action: 'interact' | 'checkpoint';
  vehicle?: JobVehicle;
  /** A recovery pickup follows this real vehicle's current server position. targetId supplies a fallback label. */
  targetVehicleId?: string;
  requiresCargo?: boolean;
  grantCargo?: boolean;
  consumeCargo?: boolean;
  /** Absolute vehicle speed in simulation metres per second. */
  maxSpeed?: number;
  minimumSeconds?: number;
  /** Authored receipt revealed after this stage; it carries no executable effect. */
  event?: { title: string; body: string };
}
export interface JobCrewTip { role: 'driver' | 'navigator' | 'runner'; text: string }
export interface JobDefinition {
  id: string;
  title: string;
  description: string;
  kind: JobKind;
  reward: JobReward;
  cooldownSeconds: number;
  minReputation?: number;
  /** Completion is recorded durably; a finished case cannot be accepted again. */
  once?: boolean;
  requiresJobs?: string[];
  /** Successful completion adds one case to this sector, independently of project points. */
  sector?: CitySector;
  /** When present, measured from job acceptance by the authoritative simulation. */
  timeLimitSeconds?: number;
  crewTips?: JobCrewTip[];
  stages: JobStage[];
}

export const CITY_EXPOSE_JOB_ID = 'media-correction';
export const CITY_SECTORS: readonly { id: CitySector; label: string; description: string }[] = [
  { id: 'energy', label: 'Energy', description: 'Deliver clinic lamps and reconcile the maintenance invoice with the service record.' },
  { id: 'welfare', label: 'Welfare', description: 'Compare the meal allocation and dispatch counts, then deliver the replacement crates.' },
  { id: 'resources', label: 'Natural resources', description: 'Compare the river-haul permit with the steward’s signed manifest.' },
  { id: 'procurement', label: 'Public contracts', description: 'Put the changed tender and disclosed media sponsorship on the same public record.' },
];
export const CITY_ROUTES: Record<CityRoute, { label: string; description: string; consequence: string }> = {
  reform: {
    label: 'Publish the full case',
    description: 'Bind the next administration to the same disclosure rules. Include Samar’s sponsor annex.',
    consequence: 'Permanent for this city save: future jobs that contribute to projects give +1 project point. Credits and reputation keep their normal values.',
  },
  capture: {
    label: 'Take Samar’s deal',
    description: 'Seal the sponsor annex, betray Noor’s agreement and give Samar’s backers a private route into the new administration.',
    consequence: 'Permanent for this city save: future jobs give 25% more crew credits, rounded down, but zero project points. Credits are a shared score; they cannot currently be spent. Reputation is unchanged.',
  },
};
export const CITY_OUTCOMES: Record<CityRoute, { id: string; title: string; description: string }> = {
  reform: {
    id: 'open-mandate', title: 'Open Mandate',
    description: 'The council releases the case, removes the administration through a recorded vote and appoints an interim coalition under published contracts. Noor prints Samar’s disclosures too. Meera waits until the ceremony ends, then hands you tomorrow’s delivery list. The new government must answer to the same rules.',
  },
  capture: {
    id: 'new-name-on-the-door', title: 'A New Name on the Door',
    description: 'The administration falls, but Samar’s backers gain a private channel. You seal their annex and keep the lucrative dispatches. Noor refuses to endorse the deal. On Republic Times, Grnab Aoswami announces a fresh beginning beneath familiar sponsor credits. The names on the doors change; the favors continue.',
  },
};
/** Original in-world satire, not a live news feed or measured internet trends. */
export const CITY_MEDIA_CARDS: readonly { id: string; outlet: string; speaker: string; title: string; body: string; requiresJobs?: string[] }[] = [
  {
    id: 'studio-certainty', outlet: 'Republic Times', speaker: 'Grnab Aoswami',
    title: 'EVERY SHELF FULL. EVERY QUESTION PREMATURE.',
    body: 'Tonight’s broadcast counts the crates behind the presenter. Noor would like to count the ones at the clinic. Start The Nine O’Clock Correction to check the difference.',
  },
  {
    id: 'correction-corner', outlet: 'Republic Times', speaker: 'Grnab Aoswami', requiresJobs: [CITY_EXPOSE_JOB_ID],
    title: 'CORRECTION: THE SHELVES WERE IN OUR STUDIO.',
    body: 'Our earlier claim has moved to a smaller font. Independent analysis will resume immediately after this message from Bright Meridian Services.',
  },
  {
    id: 'invoice-applause', outlet: 'The Lantern', speaker: 'Noor', requiresJobs: ['sector-energy'],
    title: 'THE LIGHTS ARE ON. THE INVOICE WANTS APPLAUSE.',
    body: 'The crew delivered the lamps. The old invoice still has to explain what it charged for. A useful service and an unanswered bill can exist on the same page.',
  },
  {
    id: 'breakfast-headline', outlet: 'Republic Times', speaker: 'Grnab Aoswami', requiresJobs: ['sector-welfare'],
    title: 'TOMORROW’S BREAKFAST ARRIVES IN TODAY’S HEADLINE.',
    body: 'The headline was punctual. The meal crates needed a van. Meera has requested that future announcements include breakfast.',
  },
  {
    id: 'river-footnote', outlet: 'The Lantern', speaker: 'Meera', requiresJobs: ['sector-resources'],
    title: 'THE RIVER HAS ASKED TO SEE THE FOOTNOTES.',
    body: 'A renewal slogan is not a haul permit. The public limit and signed manifest now sit beside one another in the case file.',
  },
  {
    id: 'sponsor-break', outlet: 'Republic Times', speaker: 'Grnab Aoswami', requiresJobs: ['sector-procurement'],
    title: 'INDEPENDENT ANALYSIS, PROUDLY INTERRUPTED BY OUR SPONSOR.',
    body: 'The changed tender and the sponsorship dates are public. The Lantern has requested the contractor’s response. Our studio has requested a longer ad break.',
  },
];

/** The client preview and authoritative payout must use the same route-dependent arithmetic. */
export function getEffectiveJobReward(base: JobReward, route: CityRoute | null): JobReward {
  if (route === 'capture') return { credits: Math.floor(base.credits * 1.25), reputation: base.reputation, project: 0 };
  if (route === 'reform') return { ...base, project: base.project > 0 ? base.project + 1 : 0 };
  return { ...base };
}

export interface ProjectMilestone {
  level: number;
  threshold: number;
  title: string;
  description: string;
}
export const PROJECT_MILESTONES: readonly ProjectMilestone[] = [
  { level: 0, threshold: 0, title: 'Starting Out', description: 'Complete supply jobs to add contributions to this district’s project board.' },
  { level: 1, threshold: 3, title: 'First Contributions', description: 'Three contributions recorded. The crew has completed its first project target.' },
  { level: 2, threshold: 8, title: 'Regular Support', description: 'Eight contributions recorded. The crew is keeping local projects supplied.' },
  { level: 3, threshold: 15, title: 'Neighbourhood Backbone', description: 'Fifteen contributions recorded. Further jobs continue adding to the district total.' },
];

/** Milestones are room progress, not global accounts, purchases or a simulated political outcome. */
export function getProjectLevel(project: number): number {
  if (!Number.isFinite(project)) return 0;
  return PROJECT_MILESTONES.reduce((level, milestone) => project >= milestone.threshold ? milestone.level : level, 0);
}

export const CONTRACTS: JobDefinition[] = [
  {
    id: 'clinic-restock', title: 'Clinic Restock', kind: 'delivery', minReputation: 0,
    description: 'Kavya needs the next supply load. Bring the van to Mill Ward, collect it, then park at Night Clinic for an on-foot handover.',
    reward: { credits: 100, reputation: 2, project: 1 }, cooldownSeconds: 30,
    crewTips: [
      { role: 'driver', text: 'Use the van for the whole load. Stop inside the marked pickup and delivery areas.' },
      { role: 'navigator', text: 'Call out the clinic route while the driver collects the load.' },
      { role: 'runner', text: 'At the clinic, step out and unload while the driver keeps the van parked nearby.' },
    ],
    stages: [
      { id: 'load', objective: 'Park the van at Mill Ward. From the driver’s seat, interact to load clinic supplies.', targetId: 'mill', action: 'interact', vehicle: 'van', grantCargo: true, maxSpeed: 1.5 },
      { id: 'drive', objective: 'Drive the loaded van to Night Clinic and stop inside the delivery area.', targetId: 'clinic', action: 'checkpoint', vehicle: 'van', requiresCargo: true, maxSpeed: 1.5 },
      { id: 'unload', objective: 'On foot at Night Clinic, interact to unload. Keep the same van parked in the delivery area.', targetId: 'clinic', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5 },
    ],
  },
  {
    id: 'pool-car-recall', title: 'Pool Car Recall', kind: 'recovery', minReputation: 0,
    description: 'Yusuf’s compact needs collecting after its last shift. Find the actual parked car, take it through Mill Ward, then return it to the garage.',
    reward: { credits: 120, reputation: 2, project: 0 }, cooldownSeconds: 60,
    crewTips: [
      { role: 'driver', text: 'After the pickup check, take the compact through Mill Ward and back to Yusuf’s Garage.' },
      { role: 'navigator', text: 'The first marker follows the car’s real position; it may have moved since your last job.' },
      { role: 'runner', text: 'Approach the stopped, empty compact on foot to claim the pickup. Ask any occupants to exit first.' },
    ],
    stages: [
      { id: 'locate', objective: 'Find the marked compact. On foot beside it, interact when it is stopped and empty.', targetId: 'garage', targetVehicleId: 'compact-01', action: 'interact', vehicle: 'none', maxSpeed: 1.5 },
      { id: 'check', objective: 'Drive the claimed compact through the Mill Ward checkpoint.', targetId: 'mill', action: 'checkpoint', vehicle: 'car' },
      { id: 'return', objective: 'Park the same compact at Yusuf’s Garage. From the driver’s seat, interact to finish the return.', targetId: 'garage', action: 'interact', vehicle: 'car', maxSpeed: 1.5 },
    ],
  },
  {
    id: 'district-circuit', title: 'District Circuit', kind: 'circuit', minReputation: 0,
    description: 'Yusuf has marked a practice route around the district. Check in at the garage, follow the checkpoints in order and return within three minutes of accepting.',
    reward: { credits: 80, reputation: 2, project: 0 }, cooldownSeconds: 30, timeLimitSeconds: 180,
    crewTips: [
      { role: 'driver', text: 'Use one car for the full circuit. Finish parked at the garage before the timer expires.' },
      { role: 'navigator', text: 'Call the next turn: Mill Ward, City Records, Open Frequency, River Steps, then the garage.' },
      { role: 'runner', text: 'No unloading is required. Ride along or help the crew locate its car before accepting.' },
    ],
    stages: [
      { id: 'check-in', objective: 'Park a car at Yusuf’s Garage. Interact from the driver’s seat to check in.', targetId: 'garage', action: 'interact', vehicle: 'car', maxSpeed: 1.5 },
      { id: 'mill', objective: 'Drive the same car through the Mill Ward checkpoint.', targetId: 'mill', action: 'checkpoint', vehicle: 'car' },
      { id: 'records', objective: 'Continue through the City Records checkpoint.', targetId: 'archive', action: 'checkpoint', vehicle: 'car' },
      { id: 'radio', objective: 'Continue through the Open Frequency checkpoint.', targetId: 'radio', action: 'checkpoint', vehicle: 'car' },
      { id: 'river', objective: 'Continue through the River Steps checkpoint.', targetId: 'river', action: 'checkpoint', vehicle: 'car' },
      { id: 'finish', objective: 'Return to Yusuf’s Garage and stop. Interact from the driver’s seat before time runs out.', targetId: 'garage', action: 'interact', vehicle: 'car', maxSpeed: 1.5 },
    ],
  },
  {
    id: 'print-run', title: 'Print Run', kind: 'delivery', minReputation: 4,
    description: 'Noor has two local editions ready. Take the print-shop bundle to the newsroom, collect the community notices there, then deliver them to Assembly Square.',
    reward: { credits: 140, reputation: 3, project: 1 }, cooldownSeconds: 45,
    crewTips: [
      { role: 'driver', text: 'Either vehicle works. Keep the same vehicle through both loads and stop for each handover.' },
      { role: 'navigator', text: 'Plan both legs: Open Frequency to The Newsroom, then Assembly Square.' },
      { role: 'runner', text: 'Unload on foot at each stop. The driver loads the next bundle only after the previous handover.' },
    ],
    stages: [
      { id: 'load-edition', objective: 'Park a vehicle at Open Frequency. Interact from the driver’s seat to load the printed edition.', targetId: 'radio', action: 'interact', vehicle: 'any', grantCargo: true, maxSpeed: 1.5 },
      { id: 'newsroom', objective: 'On foot at The Newsroom, hand over the edition with the loaded vehicle parked nearby.', targetId: 'board', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5 },
      { id: 'load-notices', objective: 'At The Newsroom, interact from the same vehicle’s driver seat to load community notices.', targetId: 'board', action: 'interact', vehicle: 'any', grantCargo: true, maxSpeed: 1.5 },
      { id: 'square', objective: 'On foot at Assembly Square, unload the notices. Keep the same vehicle parked in the marked area.', targetId: 'square', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5 },
    ],
  },
  {
    id: 'community-build', title: 'Community Build', kind: 'civic', minReputation: 4,
    description: 'Meera’s volunteers need two material loads: depot supplies for Assembly Square, then garage fittings for River Steps. Both deliveries count toward the district project.',
    reward: { credits: 160, reputation: 3, project: 2 }, cooldownSeconds: 60,
    crewTips: [
      { role: 'driver', text: 'Bring the van. Collect the first load at Mill Ward and the second at Yusuf’s Garage.' },
      { role: 'navigator', text: 'Plan a four-stop run: Mill Ward, Assembly Square, Yusuf’s Garage, River Steps.' },
      { role: 'runner', text: 'Unload each load on foot beside the parked van. The second delivery finishes the job.' },
    ],
    stages: [
      { id: 'load-supplies', objective: 'Park the van at Mill Ward. Interact from the driver’s seat to load project supplies.', targetId: 'mill', action: 'interact', vehicle: 'van', grantCargo: true, maxSpeed: 1.5 },
      { id: 'square', objective: 'On foot at Assembly Square, unload the supplies with the same van parked in the marked area.', targetId: 'square', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5 },
      { id: 'load-fittings', objective: 'Park the same van at Yusuf’s Garage. Interact from the driver’s seat to load the fittings.', targetId: 'garage', action: 'interact', vehicle: 'van', grantCargo: true, maxSpeed: 1.5 },
      { id: 'river', objective: 'On foot at River Steps, unload the fittings with the van parked nearby to complete both deliveries.', targetId: 'river', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5 },
    ],
  },
  {
    id: CITY_EXPOSE_JOB_ID, title: 'The Nine O’Clock Correction', kind: 'delivery', minReputation: 0, once: true,
    description: 'Republic Times says every clinic shelf is full. Help Noor check the claim: take the records to Kavya, then deliver the correction. Opens four city cases.',
    reward: { credits: 120, reputation: 2, project: 1 }, cooldownSeconds: 0,
    crewTips: [
      { role: 'driver', text: 'After the newsroom briefing, use either vehicle for both record loads. Keep the same vehicle for the whole case.' },
      { role: 'navigator', text: 'Call the route: The Newsroom, City Records, Night Clinic, then Open Frequency. Earned receipts remain on the case board.' },
      { role: 'runner', text: 'Take the briefing on foot. Unload for Kavya, let the driver collect the checked packet, then hand it over at Open Frequency.' },
    ],
    stages: [
      { id: 'brief', objective: 'On foot at The Newsroom, speak with Noor about the Republic Times delivery claim.', targetId: 'board', action: 'interact', vehicle: 'none', event: { title: 'A shelf behind the presenter', body: 'Noor: “Grnab counted the crates in his studio shot. Let’s check what arrived at Night Clinic.” Pick up the dispatch and airtime copies at City Records.' } },
      { id: 'archive-load', objective: 'Park either vehicle at City Records. From the driver’s seat, load the authorized dispatch and airtime copies.', targetId: 'archive', action: 'interact', vehicle: 'any', grantCargo: true, maxSpeed: 1.5, event: { title: 'Twelve for the camera', body: 'Twelve crates went to Bright Meridian’s media display; Republic Times was paid to cover it. Noor: “An excellent delivery. To a television studio.” Kavya has the clinic’s receipt.' } },
      { id: 'clinic-check', objective: 'On foot at Night Clinic, unload the records for Kavya. Keep the loaded vehicle parked nearby.', targetId: 'clinic', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5, event: { title: 'Four for the night desk', body: 'Kavya signs for four clinic crates, not the twelve behind Grnab. “My shelves don’t get fuller when he raises his voice.” Noor puts both destinations in the correction.' } },
      { id: 'clinic-load', objective: 'At Night Clinic, interact from the same vehicle’s driver seat to load Kavya’s checked correction packet.', targetId: 'clinic', action: 'interact', vehicle: 'any', grantCargo: true, maxSpeed: 1.5, event: { title: 'A correction with its working', body: 'The two receipts and a request for Republic Times’ response are packed. Noor has found four more files: energy, meals, river hauling and public contracts. First, get this correction to Open Frequency.' } },
      { id: 'broadcast', objective: 'On foot at Open Frequency, unload the correction packet beside the parked vehicle for publication.', targetId: 'radio', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5, event: { title: 'The correction goes public', body: 'The Lantern publishes both counts. Grnab announces: “The shelves were, technically, in our studio.” Four sector cases are now open on the job board.' } },
    ],
  },
  {
    id: 'sector-energy', title: 'Light, Camera, Invoice', kind: 'civic', minReputation: 0, once: true, requiresJobs: [CITY_EXPOSE_JOB_ID], sector: 'energy',
    description: 'Deliver Yusuf’s service lamps to Night Clinic, then take its acknowledgment and Bright Meridian’s installation invoice to the public hearing desk.',
    reward: { credits: 180, reputation: 3, project: 2 }, cooldownSeconds: 0,
    crewTips: [
      { role: 'driver', text: 'Use one van for both loads: garage service kit, then clinic report.' },
      { role: 'navigator', text: 'Guide the van from Yusuf’s Garage to Night Clinic, then Public Hearing.' },
      { role: 'runner', text: 'Unload the lamps on foot before the driver collects the report. File the final bundle on foot at Public Hearing.' },
    ],
    stages: [
      { id: 'load-lamps', objective: 'Park the van at Yusuf’s Garage. From the driver’s seat, load the service lamps and invoice copy.', targetId: 'garage', action: 'interact', vehicle: 'van', grantCargo: true, maxSpeed: 1.5, event: { title: 'A bill for installed fixtures', body: 'Yusuf packs four portable lamps beside an invoice for twelve installed clinic fixtures. “The invoice works perfectly. Shame about the lighting.” Kavya has the installation log.' } },
      { id: 'clinic-service', objective: 'On foot at Night Clinic, unload the service lamps beside the stopped van.', targetId: 'clinic', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5, event: { title: 'Light now, answers next', body: 'Kavya signs for your four portable lamps. Her earlier installation log records four fixtures against Bright Meridian’s bill for twelve. Eight billed fixtures are missing from the service record.' } },
      { id: 'load-report', objective: 'At Night Clinic, load the signed energy-service file from the same van’s driver seat.', targetId: 'clinic', action: 'interact', vehicle: 'van', grantCargo: true, maxSpeed: 1.5, event: { title: 'Two services kept separate', body: 'Noor staples the old invoice to its installation log and keeps today’s delivery separate. Bright Meridian receives a request to explain the eight-fixture difference. Kavya: “They can send the answer with the missing lights.”' } },
      { id: 'file-energy', objective: 'On foot at Public Hearing, unload the energy-service file beside the parked van.', targetId: 'civic', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5, event: { title: 'Energy case filed', body: 'The hearing desk logs the missing fixtures and response request. Noor’s caption: “The lights are on. The invoice would like a standing ovation.” Energy case complete.' } },
    ],
  },
  {
    id: 'sector-welfare', title: 'The Missing Breakfast', kind: 'delivery', minReputation: 0, once: true, requiresJobs: [CITY_EXPOSE_JOB_ID], sector: 'welfare',
    description: 'Compare the meal allocation with Mill Ward’s release slip, collect the authorized replacement crates and deliver them to Meera at Assembly Square.',
    reward: { credits: 160, reputation: 3, project: 2 }, cooldownSeconds: 0,
    crewTips: [
      { role: 'driver', text: 'Either vehicle can carry the records and replacement crates. Keep it for both loads.' },
      { role: 'navigator', text: 'Plan City Records to Mill Ward, then Assembly Square. The second stop includes a new load before departure.' },
      { role: 'runner', text: 'Unload the record at Mill Ward, then hand the replacement crates to Meera on foot at Assembly Square.' },
    ],
    stages: [
      { id: 'load-register', objective: 'Park either vehicle at City Records. From the driver’s seat, load the aggregate meal allocation record.', targetId: 'archive', action: 'interact', vehicle: 'any', grantCargo: true, maxSpeed: 1.5, event: { title: 'Breakfast by the crate', body: 'The allocation promises twelve meal crates for Assembly Square. Meera says the tables came up short. Mill Ward holds the release slip.' } },
      { id: 'depot-check', objective: 'On foot at Mill Ward, unload the allocation record beside the parked vehicle for comparison.', targetId: 'mill', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5, event: { title: 'The amended count', body: 'The release slip cut twelve crates to eight. Republic Times kept the larger number in its breakfast special. The depot authorizes four replacements and attaches the amendment for review.' } },
      { id: 'load-meals', objective: 'At Mill Ward, load the four replacement meal crates from the same vehicle’s driver seat.', targetId: 'mill', action: 'interact', vehicle: 'any', grantCargo: true, maxSpeed: 1.5, event: { title: 'A van instead of a headline', body: 'Four replacement crates are loaded. Meera: “Keep the paperwork. Bring breakfast too.”' } },
      { id: 'square-handover', objective: 'On foot at Assembly Square, unload the replacement meal crates beside the stopped vehicle.', targetId: 'square', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5, event: { title: 'Breakfast received', body: 'Meera signs for the replacements and files the unexplained cut. Grnab promises tomorrow’s breakfast is already breaking news. Welfare case complete.' } },
    ],
  },
  {
    id: 'sector-resources', title: 'The River Has Receipts', kind: 'delivery', minReputation: 0, once: true, requiresJobs: [CITY_EXPOSE_JOB_ID], sector: 'resources',
    description: 'Take the public river-haul permit to River Steps, compare it with the steward’s signed manifest and bring the checked file to Public Hearing.',
    reward: { credits: 170, reputation: 3, project: 1 }, cooldownSeconds: 0,
    crewTips: [
      { role: 'driver', text: 'Use the same car or van for the permit and the checked river file.' },
      { role: 'navigator', text: 'Guide the crew from City Records to River Steps and then Public Hearing.' },
      { role: 'runner', text: 'Unload each document bundle on foot beside its parked vehicle. Let the driver collect the checked river file before leaving River Steps.' },
    ],
    stages: [
      { id: 'load-permit', objective: 'Park either vehicle at City Records. From the driver’s seat, load the public river-haul permit.', targetId: 'archive', action: 'interact', vehicle: 'any', grantCargo: true, maxSpeed: 1.5, event: { title: 'A slogan with a limit', body: 'Bright Meridian’s renewal permit allows six aggregate loads from River Steps this week. Meera has arranged a look at the steward’s manifest. “Renewal apparently comes with a loading bay.”' } },
      { id: 'river-check', objective: 'On foot at River Steps, unload the permit beside the stopped vehicle for the steward’s comparison.', targetId: 'river', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5, event: { title: 'Nine signed departures', body: 'Nine departures, one six-load permit, the same week. The steward signs the copy and asks where the extra three loads were authorized. Noor adds that question to the file.' } },
      { id: 'load-river-file', objective: 'At River Steps, load the checked permit and manifest from the same vehicle’s driver seat.', targetId: 'river', action: 'interact', vehicle: 'any', grantCargo: true, maxSpeed: 1.5, event: { title: 'A question with references', body: 'The permit and manifest travel together, with a request for any missing amendment. Meera: “The river has asked to see the footnotes.”' } },
      { id: 'file-resources', objective: 'On foot at Public Hearing, unload the checked river file beside the parked vehicle.', targetId: 'civic', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5, event: { title: 'The river enters the record', body: 'The hearing desk logs the three-load difference and requests Bright Meridian’s answer. A renewal slogan will not cover the permit gap. Natural-resources case complete.' } },
    ],
  },
  {
    id: 'sector-procurement', title: 'Lowest Bid, Loudest Sponsor', kind: 'delivery', minReputation: 0, once: true, requiresJobs: [CITY_EXPOSE_JOB_ID], sector: 'procurement',
    description: 'Compare two public bid rounds with Republic Times’ disclosed sponsorship contract, then submit the changed tender and response request at Public Hearing.',
    reward: { credits: 190, reputation: 3, project: 1 }, cooldownSeconds: 0,
    crewTips: [
      { role: 'driver', text: 'Either vehicle works. Carry both record bundles in the same vehicle.' },
      { role: 'navigator', text: 'Call the route from City Records to Open Frequency, then Public Hearing.' },
      { role: 'runner', text: 'Unload the bid summaries for comparison at Open Frequency and file the final dossier on foot at Public Hearing.' },
    ],
    stages: [
      { id: 'load-bids', objective: 'Park either vehicle at City Records. From the driver’s seat, load both public bid-round summaries.', targetId: 'archive', action: 'interact', vehicle: 'any', grantCargo: true, maxSpeed: 1.5, event: { title: 'The rule changed after closing', body: 'The service tender closed, then reopened with a compulsory broadcast package. Bright Meridian won the revised round. Noor: “Someone added a microphone to a maintenance contract.”' } },
      { id: 'sponsor-check', objective: 'On foot at Open Frequency, unload the bid summaries beside the parked vehicle to compare the disclosed sponsorship.', targetId: 'radio', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5, event: { title: 'A sponsor at the right moment', body: 'Bright Meridian sponsored Republic Times during the revised tender. Noor records the dates and asks who approved the bundled requirement. Grnab requests an ad break.' } },
      { id: 'load-dossier', objective: 'At Open Frequency, load the checked procurement file from the same vehicle’s driver seat.', targetId: 'radio', action: 'interact', vehicle: 'any', grantCargo: true, maxSpeed: 1.5, event: { title: 'Samar’s annex', body: 'Samar supplies an unpublished annex: his coalition’s advisers helped shape the revised package. “Use the rest,” he says, “but keep our supporters out of the next edition.” Noor adds the annex and his request to the working file.' } },
      { id: 'file-procurement', objective: 'On foot at Public Hearing, unload the procurement file and response request beside the parked vehicle.', targetId: 'civic', action: 'interact', vehicle: 'none', requiresCargo: true, consumeCargo: true, maxSpeed: 1.5, event: { title: 'The same test for the next government', body: 'The desk logs the working file; Samar’s annex remains unpublished until the crew’s mandate. Complete all four sectors, then return here on foot to decide what becomes public. Public-contracts case complete.' } },
    ],
  },
];
