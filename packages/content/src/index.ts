/** Original fictional campaign data. Nothing in this module executes uploaded scripts. */
export const CONTENT_VERSION = '0.5.0';

export interface CampaignMetrics { trust: number; care: number; accountability: number }
export type LandmarkId = 'garage' | 'board' | 'clinic' | 'archive' | 'mill' | 'radio' | 'square' | 'civic' | 'river';
export interface DialogueLine { speaker: string; text: string }
export interface MissionChoice {
  id: string;
  label: string;
  description: string;
  effects?: Partial<CampaignMetrics>;
  evidence?: string[];
  consequence?: string;
}
export interface MissionStage {
  id: string;
  objective: string;
  targetId: LandmarkId;
  trigger: 'interact' | 'arrive' | 'enter_vehicle' | 'choice';
  dialogue: DialogueLine[];
  evidence?: string[];
  choices?: MissionChoice[];
  documents?: string[];
  dialogueVariants?: { when: StoryDecision; dialogue: DialogueLine[] }[];
}
export interface Mission { id: string; title: string; description: string; stages: MissionStage[] }
export interface EvidenceDocument {
  id: string;
  title: string;
  source: string;
  body: string;
  qualification: string;
}
export interface CampaignEnding { id: string; title: string; description: string }
export interface StoryDecision { chapterId: string; stageId: string; choiceId: string }

/** Exact authored history matches only; no expressions, script evaluation or arbitrary predicates. */
export function getStageDialogue(stage: MissionStage, history: readonly StoryDecision[]): DialogueLine[] {
  for (const variant of stage.dialogueVariants ?? []) {
    if (history.some(decision => decision.chapterId === variant.when.chapterId && decision.stageId === variant.when.stageId && decision.choiceId === variant.when.choiceId)) return variant.dialogue;
  }
  return stage.dialogue;
}

export function getChoiceConsequence(decision: StoryDecision): string {
  return CAMPAIGN.find(chapter => chapter.id === decision.chapterId)?.stages.find(stage => stage.id === decision.stageId)?.choices?.find(choice => choice.id === decision.choiceId)?.consequence ?? '';
}

export function getDocumentStatus(id: string, history: readonly StoryDecision[]): string {
  if (id === 'sponsor') {
    const submitted = history.some(item => item.chapterId === 'public-hearing' && item.stageId === 'hearing-choice' && item.choiceId === 'open-record');
    const disclosed = history.some(item => item.chapterId === 'first-edition' && item.stageId === 'friendly-ledger' && item.choiceId === 'disclose');
    return submitted ? 'Submitted for independent review' : disclosed ? 'Conflict disclosed publicly · wider donor file still closed' : 'Known to the crew · public disclosure not recorded';
  }
  if (id === 'hearing') return 'Crew working dossier · not an automatic public submission';
  if (id === 'orderPublic' || id === 'amendmentPublic' || id === 'copies') return 'Public record · interpretation still requires care';
  if (id === 'deliveryLog') return 'Clerk’s authorized copy · surname link ruled out';
  return 'Fictional case material · read its source and qualification';
}

export const EVIDENCE: Record<string, EvidenceDocument> = {
  delivery: {
    id: 'delivery', title: 'The last delivery', source: 'Clinic dispatch receipt · Devnagar · 14 June, Year 8',
    body: 'Shipment C-17: twelve clinic supply crates. Dispatch recorded at 18:40. Receiving desk entry: 18:10. The printed receipt bears the same shipment reference. Aadi delivered the sealed paperwork, not the missing crates.',
    qualification: 'The timestamps disagree. This alone establishes neither theft nor who altered the record.',
  },
  explanation: {
    id: 'explanation', title: 'Kavya’s working note', source: 'Clinic conversation · with permission',
    body: 'The desk clock was corrected last week. Kavya agrees to check whether the export retained an older time. A mundane error is possible; the shipment quantity still needs confirmation.',
    qualification: 'A possible explanation, not a verified correction.',
  },
  clinicCopy: {
    id: 'clinicCopy', title: 'An authorized copy', source: 'Clinic receiving desk · redacted copy',
    body: 'The receiving desk logged four crates against C-17. The public dispatch summary lists twelve. Patient names and medical information were removed before this copy was released.',
    qualification: 'Two official records disagree about quantity. The remaining eight crates have not yet been located.',
  },
  heldCopy: {
    id: 'heldCopy', title: 'Custody receipt', source: 'Kavya · clinic document desk',
    body: 'Kavya retains the sealed original and gives the crew a receipt and the C-17 reference. The newsroom can ask for the authorized public record without exposing private paperwork.',
    qualification: 'Preserving a document does not validate everything written in it.',
  },
  copies: {
    id: 'copies', title: 'Two copies, one reference', source: 'Records office · public procurement register',
    body: 'The approved order is for twelve crates. A signed amendment redirects eight to a riverfront demonstration site. Its publication date is later than the clinic delivery. Both records carry the C-17 reference.',
    qualification: 'The redirection is documented. Whether the approval and disclosure complied with the fictional city charter remains unresolved.',
  },
  orderPublic: {
    id: 'orderPublic', title: 'Order C-17 · original', source: 'City Records · public order · approved 10 June, Year 8',
    body: 'Destination: Night Clinic. Quantity: twelve supply crates. Requested dispatch: 14 June at 18:40. This order predates the amendment and does not record its later redirection.',
    qualification: 'An approved quantity is not proof that twelve crates reached the clinic.',
  },
  amendmentPublic: {
    id: 'amendmentPublic', title: 'Order C-17 · amendment', source: 'City Records · signed 13 June; published 15 June, Year 8',
    body: 'Eight of the twelve crates are redirected to the riverfront demonstration. Four remain assigned to Night Clinic. Delivery date remains 14 June. The public amendment appeared the following day.',
    qualification: 'This records redirection and late publication. It does not establish theft or tell us whether the clinic was warned.',
  },
  caution: {
    id: 'caution', title: 'A question kept open', source: 'Kavya · comparison note',
    body: 'The crew records the redirection and asks when the clinic was told. The late publication is a supported discrepancy. A signature alone cannot tell us what each person knew.',
    qualification: 'The claim is limited to what the records establish.',
  },
  allegation: {
    id: 'allegation', title: 'A claim that runs ahead', source: 'Noor · first draft, unverified',
    body: 'The first draft calls the missing crates a deliberate theft by the entire project leadership. The two records do not establish that conclusion. The draft remains here so the crew cannot quietly erase its own mistake.',
    qualification: 'Unsubstantiated allegation. Do not treat this draft as evidence of guilt.',
  },
  deliveryLog: {
    id: 'deliveryLog', title: 'A mundane name match', source: 'Mill Ward depot · shipping clerk’s copy',
    body: 'Eight crates reached the demonstration site. The courier named Sethi is a small transport cooperative, unrelated to Nalin Sethi’s company. A similar name initially made the ownership diagram misleading.',
    qualification: 'The shipping log supports the delivery route; the name match does not establish common ownership.',
  },
  dispatchPriority: {
    id: 'dispatchPriority', title: 'Dispatch first', source: 'Mill Ward depot · crew dispatch note',
    body: 'The crew prioritizes the reserve van. Replacement supplies leave for Night Clinic before the complete stock comparison. The clerk retains the inventory for later inspection.',
    qualification: 'The clinic receives help promptly; the crew has not yet verified the full depot stock count.',
  },
  witnessStatement: {
    id: 'witnessStatement', title: 'The clerk’s complete account', source: 'Mill Ward depot · consenting recorded interview',
    body: 'The clerk explains who received the redirection order and how the reserve stock was arranged. The crew stays to hear the whole account. The replacement van leaves later in the evening.',
    qualification: 'The fuller account preserves a witness’s perspective. It is not independently corroborated in every detail, and the dispatch was later.',
  },
  stockAudit: {
    id: 'stockAudit', title: 'Stock before movement', source: 'Mill Ward depot · authorized count and photographs',
    body: 'The crew and clerk compare the remaining crates with the inventory and record the count before loading. The physical record is clearer, but the short visit leaves little time for the clerk’s personal account.',
    qualification: 'The count supports what remained at the depot. It cannot explain every decision or substitute for the witness’s testimony.',
  },
  clinicRestored: {
    id: 'clinicRestored', title: 'Service before spectacle', source: 'Clinic desk · current delivery acknowledgment',
    body: 'The depot releases replacement supplies and the clinic acknowledges receipt. The immediate shortage is addressed. Meera asks the crew to keep investigating why services were used as a display prop.',
    qualification: 'Restoring supplies resolves today’s shortage. It does not settle responsibility for the original decision.',
  },
  engineer: {
    id: 'engineer', title: 'The engineer’s account', source: 'Riverfront project · consenting interview',
    body: 'Engineer Leela Roy says the demonstration genuinely improved a flood sensor. She objected to borrowing clinic stock but her note was omitted from the public summary. The project can be useful and its procurement still deserve scrutiny.',
    qualification: 'The published amendment corroborates the redirection. Her objection and the omitted note remain her attributed account.',
  },
  correction: {
    id: 'correction', title: 'A correction in the first edition', source: 'The Lantern · published editorial note',
    body: 'The crew publishes the crate redirection, the service failure and the unanswered approval question. It explicitly rejects the mistaken Sethi ownership link and labels the broader theft claim unsupported.',
    qualification: 'This makes the newsroom’s discarded assumptions visible. An unpublished draft is distinct from a public allegation.',
  },
  sponsor: {
    id: 'sponsor', title: 'The friendly ledger', source: 'Samar Dutt · accounts shown to the crew',
    body: 'Samar, finance convenor of the reform coalition, paid for the crew’s stage while receiving a consulting payment from the riverfront project. No illicit transfer is established, but the conflict should be disclosed. The coalition’s wider donor accounts have not been opened.',
    qualification: 'An acknowledged conflict of interest, not proof of bribery. The same disclosure standard applies to allies.',
  },
  hiddenSponsor: {
    id: 'hiddenSponsor', title: 'A sealed drawer', source: 'Crew decision · withheld conflict',
    body: 'The crew agrees to defer publishing Samar’s consulting payment. Their public account of who funded the event is now incomplete. Samar promises the matter can be addressed after the hearing.',
    qualification: 'This records the crew’s own choice to withhold relevant context.',
  },
  voices: {
    id: 'voices', title: 'Who gets a microphone?', source: 'Open Microphone · consented public testimony',
    body: 'Meera asks for reliable clinic services. Tara asks that residents can criticize the next administration too. Yusuf asks whether the garage will still open tomorrow. They agree on disclosure without agreeing on every policy.',
    qualification: 'These are individual fictional testimonies, not a poll or a mandate from everyone in Devnagar.',
  },
  offer: {
    id: 'offer', title: 'Asha’s offer', source: 'Chief minister’s office · public written proposal',
    body: 'Asha proposes restoring clinic supply funding and holding an internal review. The review’s full documents would remain with her office. An independent hearing could publish them, but would take longer.',
    qualification: 'The proposal contains a practical remedy and a disclosure limit. The player can judge that tradeoff.',
  },
  hearing: {
    id: 'hearing', title: 'The hearing dossier', source: 'Crew working file · prepared for Civic Hall',
    body: 'The crew’s working file distinguishes the late amendment, the clinic shortage, the innocent name match, the engineer’s account and Samar’s conflict. The final choice decides what the crew submits. Anything already disclosed remains public. The coalition’s wider donor file is still unopened.',
    qualification: 'All people, institutions, dates and documents in this campaign are fictional. Connections are not automatically culpability.',
  },
};

export const CAMPAIGN: Mission[] = [
  {
    id: 'last-delivery', title: 'Last Delivery', description: 'One favour after closing time. One record that does not add up.',
    stages: [
      { id: 'keys', objective: 'Meet Yusuf at Yusuf’s Garage and collect the keys.', targetId: 'garage', trigger: 'interact', dialogue: [
        { speaker: 'Yusuf', text: 'One delivery. Then close the shutter.' },
        { speaker: 'Aadi', text: 'You said that two deliveries ago.' },
        { speaker: 'Yusuf', text: 'The first two paid. This one is a favour.' },
      ] },
      { id: 'car', objective: 'Walk to the compact car and take the driver’s seat.', targetId: 'garage', trigger: 'enter_vehicle', dialogue: [
        { speaker: 'Noor', text: 'If you ask what is in the envelope, I have to pretend I know.' },
        { speaker: 'Aadi', text: 'Then I will not ask. Where?' },
        { speaker: 'Noor', text: 'The clinic. Before the night desk closes.' },
      ] },
      { id: 'clinic-drive', objective: 'Drive across Old Market to Night Clinic.', targetId: 'clinic', trigger: 'arrive', dialogue: [
        { speaker: 'Noor', text: 'You know everyone here?' },
        { speaker: 'Aadi', text: 'I know which shops still owe me. It looks similar from outside.' },
      ] },
      { id: 'receipt', objective: 'Stop, leave the car and speak with Kavya at Night Clinic.', targetId: 'clinic', trigger: 'choice', evidence: ['delivery'], dialogue: [
        { speaker: 'Kavya', text: 'This was filed yesterday.' },
        { speaker: 'Noor', text: 'It was printed this afternoon.' },
        { speaker: 'Kavya', text: 'That is a question. Do not make it an answer yet.' },
      ], choices: [
        { id: 'ask', label: 'Ask for an explanation', description: 'Give Kavya time to check the clock. Build trust; leave the quantity unresolved.', effects: { trust: 8, accountability: 2 }, evidence: ['explanation'], consequence: 'Kavya will check the desk clock. The shipment quantity is still an open question.' },
        { id: 'copy', label: 'Request an authorized copy', description: 'Obtain a redacted desk record. The shortage becomes clearer.', effects: { accountability: 10, care: 2 }, evidence: ['clinicCopy'], consequence: 'You leave with a redacted receiving record: four crates, against twelve dispatched.' },
        { id: 'leave', label: 'Leave the original with Kavya', description: 'Protect private paperwork and take a custody receipt.', effects: { care: 10, trust: 4 }, evidence: ['heldCopy'], consequence: 'Kavya keeps the original safely. Your custody receipt retains the C-17 reference.' },
      ] },
      { id: 'river-return', objective: 'Pass River Steps on your way home.', targetId: 'river', trigger: 'arrive', dialogue: [
        { speaker: 'Radio', text: 'Devnagar’s new riverfront: a brighter tomorrow, today.' },
        { speaker: 'Kavya', text: 'Tomorrow can wait. The clinic needed those supplies this morning.' },
      ], dialogueVariants: [
        { when: { chapterId: 'last-delivery', stageId: 'receipt', choiceId: 'ask' }, dialogue: [
          { speaker: 'Noor', text: 'You gave her a chance to explain.' },
          { speaker: 'Aadi', text: 'A clock can be wrong. The empty shelf still needs an answer.' },
        ] },
        { when: { chapterId: 'last-delivery', stageId: 'receipt', choiceId: 'copy' }, dialogue: [
          { speaker: 'Noor', text: 'Four crates received. Twelve on the order. Now we have something we can check.' },
          { speaker: 'Aadi', text: 'And eight crates we cannot put back with a headline.' },
        ] },
        { when: { chapterId: 'last-delivery', stageId: 'receipt', choiceId: 'leave' }, dialogue: [
          { speaker: 'Noor', text: 'No dramatic envelope in my bag, then.' },
          { speaker: 'Aadi', text: 'We have the reference. We can ask for the public copy.' },
        ] },
      ] },
      { id: 'first-pin', objective: 'Return to The Newsroom board at the garage and pin the discrepancy.', targetId: 'board', trigger: 'interact', dialogue: [
        { speaker: 'Meera', text: 'They told me the record was complete.' },
        { speaker: 'Kavya', text: 'We have two versions.' },
        { speaker: 'Meera', text: 'Then start there. Not with a speech.' },
      ] },
    ],
  },
  {
    id: 'two-copies', title: 'Two Copies', description: 'A public record opens a door. It does not name the guilty.',
    stages: [
      { id: 'records', objective: 'Visit City Records and ask for the public amendment.', targetId: 'archive', trigger: 'arrive', dialogue: [
        { speaker: 'Kavya', text: 'The C-17 amendment is public. We can ask for it like anyone else.' },
      ] },
      { id: 'compare', objective: 'Compare the original order with its amendment.', targetId: 'archive', trigger: 'choice', evidence: ['copies', 'orderPublic', 'amendmentPublic'], documents: ['orderPublic', 'amendmentPublic'], dialogue: [
        { speaker: 'Records clerk', text: 'Twelve ordered. Eight redirected. The amendment was published after delivery.' },
        { speaker: 'Noor', text: 'So the paper trail is real. Our first explanation still might be wrong.' },
      ], choices: [
        { id: 'narrow', label: 'Record the discrepancy', description: 'Name what is established and keep the approval question open.', effects: { accountability: 12, trust: 5 }, evidence: ['caution'], consequence: 'The board records redirection and late publication. Responsibility remains an open question.' },
        { id: 'headline', label: 'Write the explosive draft', description: 'Call it theft before the witnesses have spoken. You will need to account for that claim.', effects: { accountability: -16, trust: -10 }, evidence: ['allegation'], consequence: 'Your unpublished draft calls it theft. The archive marks that conclusion unsupported.' },
        { id: 'listen', label: 'Ask who was affected', description: 'Start with the clinic’s missing supplies; bring the records to the depot next.', effects: { care: 10, trust: 5 }, evidence: ['caution'], consequence: 'The clinic’s shortage becomes your next priority. The records are preserved for comparison.' },
      ] },
      { id: 'board-copies', objective: 'Bring the two copies to The Newsroom board.', targetId: 'board', trigger: 'interact', dialogue: [
        { speaker: 'Aadi', text: 'A line between two names can look a lot like an answer.' },
        { speaker: 'Kavya', text: 'Then label the line. What connects them, and what does not?' },
      ] },
    ],
  },
  {
    id: 'empty-shelves', title: 'Empty Shelves', description: 'Follow the supplies. Remember who needs them.',
    stages: [
      { id: 'depot', objective: 'Reach the Mill Ward supply depot.', targetId: 'mill', trigger: 'arrive', dialogue: [
        { speaker: 'Aadi', text: 'I have delivered here for years. We should have asked the clerk first.' },
      ] },
      { id: 'shipping', objective: 'Talk to the shipping clerk and choose your next priority.', targetId: 'mill', trigger: 'choice', evidence: ['deliveryLog'], dialogue: [
        { speaker: 'Shipping clerk', text: 'Sethi Transport is a cooperative. No relation to the magnate. Eight crates went to the demonstration.' },
        { speaker: 'Noor', text: 'One useful fact. One wrong connection to undo.' },
      ], choices: [
        { id: 'supplies', label: 'Put the reserve van first', description: 'Send clinic supplies now. Leave the full stock comparison for another visit.', effects: { care: 14, trust: 2, accountability: -4 }, evidence: ['dispatchPriority'], consequence: 'The van leaves promptly. The clinic gains time; your depot count remains incomplete.' },
        { id: 'interview', label: 'Hear the clerk’s full account', description: 'Preserve the overlooked witness’s testimony. The reserve van will leave later.', effects: { care: -4, trust: 12, accountability: 6 }, evidence: ['witnessStatement'], consequence: 'The clerk entrusts you with the full account. The clinic waits for the later dispatch.' },
        { id: 'photo', label: 'Document the stock with the clerk', description: 'Make an authorized count and photo record. There is less time for a personal interview.', effects: { care: 3, trust: -3, accountability: 14 }, evidence: ['stockAudit'], consequence: 'The stock count is recorded before loading. The clerk’s personal account remains unheard.' },
      ] },
      { id: 'clinic-restored', objective: 'Return to Night Clinic with the depot’s delivery acknowledgment.', targetId: 'clinic', trigger: 'interact', evidence: ['clinicRestored'], dialogue: [
        { speaker: 'Kavya', text: 'After our visit, the clerk sent a van from the depot reserve. These replacements have arrived.' },
        { speaker: 'Meera', text: 'Thank you. But people should not need a journalist to get a delivery.' },
        { speaker: 'Aadi', text: 'Tomorrow, we ask why. Today, the desk can open.' },
      ], dialogueVariants: [
        { when: { chapterId: 'empty-shelves', stageId: 'shipping', choiceId: 'supplies' }, dialogue: [
          { speaker: 'Meera', text: 'The reserve van came early enough for the evening desk. Thank you.' },
          { speaker: 'Kavya', text: 'We still owe the depot a full stock check. Helping today did not answer every question.' },
        ] },
        { when: { chapterId: 'empty-shelves', stageId: 'shipping', choiceId: 'interview' }, dialogue: [
          { speaker: 'Meera', text: 'The clerk’s reserve van finally arrived. We had to keep the desk waiting.' },
          { speaker: 'Aadi', text: 'We stayed to hear his full account. I will not pretend the delay cost you nothing.' },
        ] },
        { when: { chapterId: 'empty-shelves', stageId: 'shipping', choiceId: 'photo' }, dialogue: [
          { speaker: 'Kavya', text: 'The reserve van arrived after the count. The inventory and photographs agree.' },
          { speaker: 'Meera', text: 'A record helps. Go back and hear the clerk’s story too, when you can.' },
        ] },
      ] },
      { id: 'engineer', objective: 'Meet engineer Leela Roy at River Steps.', targetId: 'river', trigger: 'interact', evidence: ['engineer'], dialogue: [
        { speaker: 'Leela', text: 'The flood sensor works. Borrowing clinic supplies was still wrong. You can write both.' },
        { speaker: 'Noor', text: 'That makes a harder headline.' },
        { speaker: 'Leela', text: 'It makes a truer one.' },
      ] },
    ],
  },
  {
    id: 'first-edition', title: 'First Edition', description: 'The city will read your words. Your friends should be able to read your accounts.',
    stages: [
      { id: 'press', objective: 'Take the reporting to the Open Frequency print shop.', targetId: 'radio', trigger: 'arrive', dialogue: [
        { speaker: 'Noor', text: 'The Lantern has one page tonight. Let us make every sentence earn its place.' },
      ] },
      { id: 'edition', objective: 'Choose what The Lantern will publish.', targetId: 'radio', trigger: 'choice', dialogue: [
        { speaker: 'Kavya', text: 'The shipment was redirected. The name match was innocent. Our own draft must say so.' },
        { speaker: 'Noor', text: 'My first notes joined those names before I checked. The article has not run. Readers can still see how we got it right.' },
      ], choices: [
        { id: 'correct', label: 'Publish the finding and correction', description: 'Explain the service failure and withdraw the unsupported connection openly.', effects: { accountability: 14, trust: 8 }, evidence: ['correction'], consequence: 'The Lantern prints the finding and the discarded name match. Readers can follow your reasoning.' },
        { id: 'quiet', label: 'Publish a shorter service story', description: 'Focus on the shortage and repair. Leave the newsroom’s discarded assumptions out.', effects: { accountability: 2, care: 5 }, consequence: 'The article explains the shortage and replacement delivery. The reporting process stays in the crew’s notes.' },
        { id: 'double', label: 'Keep the sweeping accusation', description: 'A stronger headline with weaker support. The record will challenge you later.', effects: { accountability: -18, trust: -12 }, evidence: ['allegation'], consequence: 'The accusation is now public. Your own archive still marks its wider conclusion unsupported.' },
      ] },
      { id: 'friendly-ledger', objective: 'Meet Samar at The Newsroom board and discuss the event funding.', targetId: 'board', trigger: 'choice', evidence: ['sponsor'], dialogue: [
        { speaker: 'Samar', text: 'Yes, the project paid me as a consultant. I paid for your stage. Separate things.' },
        { speaker: 'Kavya', text: 'Then publishing both should not be a problem.' },
        { speaker: 'Samar', text: 'Can accountability wait until we win?' },
      ], choices: [
        { id: 'disclose', label: 'Disclose the conflict', description: 'Apply the same standard to an ally. Keep the stage; publish the context.', effects: { accountability: 15, trust: 5 }, consequence: 'Samar’s consulting conflict is public. The coalition’s wider donor accounts remain unopened.' },
        { id: 'return', label: 'Return the sponsorship', description: 'Hold a smaller event funded by the crew. Aadi gives up the garage repairs.', effects: { accountability: 9, care: -3, trust: 3 }, consequence: 'The crew funds a smaller stage. The garage repair budget pays the difference.' },
        { id: 'conceal', label: 'Keep it between friends', description: 'Preserve the coalition today by withholding a relevant conflict.', effects: { accountability: -22, trust: -8 }, evidence: ['hiddenSponsor'], consequence: 'The event goes ahead, but the public funding account omits the conflict known to your crew.' },
      ] },
    ],
  },
  {
    id: 'open-microphone', title: 'Open Microphone', description: 'A square full of people is more than one voice.',
    stages: [
      { id: 'square', objective: 'Join the evening gathering at Assembly Square.', targetId: 'square', trigger: 'arrive', dialogue: [
        { speaker: 'Tara', text: 'We agree that something must change. Do not mistake that for agreeing on everything.' },
      ], dialogueVariants: [
        { when: { chapterId: 'first-edition', stageId: 'friendly-ledger', choiceId: 'disclose' }, dialogue: [
          { speaker: 'Tara', text: 'I read the funding note. I disagree with taking his money, but at least I can see it.' },
          { speaker: 'Noor', text: 'The microphone is yours too. Agreement is not the price of entry.' },
        ] },
        { when: { chapterId: 'first-edition', stageId: 'friendly-ledger', choiceId: 'return' }, dialogue: [
          { speaker: 'Yusuf', text: 'Smaller stage. Same voices. And the garage shutter still sticks.' },
          { speaker: 'Aadi', text: 'I know what we spent. I will make the repairs wait.' },
        ] },
        { when: { chapterId: 'first-edition', stageId: 'friendly-ledger', choiceId: 'conceal' }, dialogue: [
          { speaker: 'Tara', text: 'Who paid for all this? The leaflet does not say.' },
          { speaker: 'Kavya', text: 'We left something out. That question will follow us into the hearing.' },
        ] },
      ] },
      { id: 'voices', objective: 'Decide whose concerns enter the public record.', targetId: 'square', trigger: 'choice', evidence: ['voices'], dialogue: [
        { speaker: 'Meera', text: 'I want the clinic open after the cameras leave.' },
        { speaker: 'Tara', text: 'And I want to be allowed to disagree with whoever comes next.' },
      ], choices: [
        { id: 'share', label: 'Share the microphone', description: 'Give the clinic, workshop and dissenting residents their own words.', effects: { trust: 14, care: 10, accountability: 3 }, consequence: 'The gathering preserves several voices. Tara stays, with her disagreements intact.' },
        { id: 'services', label: 'Focus on a service guarantee', description: 'Keep the event narrow: clinics, disclosure and a date for review.', effects: { care: 14, accountability: 4, trust: 3 }, consequence: 'The event asks for reliable services and a review date. Its broader disagreements remain unresolved.' },
        { id: 'one-voice', label: 'Read one approved statement', description: 'A clean message, with disagreement kept off stage. Tara steps away.', effects: { trust: -20, accountability: -8 }, consequence: 'One statement represents the gathering. Tara leaves after her dissent is excluded.' },
      ] },
      { id: 'offer', objective: 'Collect the chief minister’s written response at Open Frequency.', targetId: 'radio', trigger: 'interact', evidence: ['offer'], dialogue: [
        { speaker: 'Asha’s statement', text: 'Supplies will be restored. My office will conduct the review and retain the complete file.' },
        { speaker: 'Noor', text: 'A remedy. And a locked drawer. We need to decide what we can accept.' },
      ] },
    ],
  },
  {
    id: 'public-hearing', title: 'The Public Hearing', description: 'Changing the name on the door is only the beginning.',
    stages: [
      { id: 'hearing-arrival', objective: 'Bring the crew’s record to the Public Hearing at Civic Hall.', targetId: 'civic', trigger: 'arrive', dialogue: [
        { speaker: 'Aadi', text: 'I thought the hard part would be getting here.' },
        { speaker: 'Kavya', text: 'Now we have to say what we know. And what we do not.' },
      ] },
      { id: 'hearing-choice', objective: 'Review the case, then choose what enters the public record.', targetId: 'civic', trigger: 'choice', evidence: ['hearing'], documents: ['copies', 'deliveryLog', 'sponsor', 'hearing'], dialogue: [
        { speaker: 'Panel chair', text: 'The record is open. What outcome are you asking this hearing to consider?' },
        { speaker: 'Meera', text: 'Whatever happens in this room, people will need the clinic in the morning.' },
      ], choices: [
        { id: 'open-record', label: 'An open, independent review', description: 'Publish the supported case, including your own mistakes. Seek responsibility and a service guarantee.', effects: { accountability: 15, trust: 5, care: 5 }, consequence: 'The crew submits its full account, including its own conflict. The review’s outcome depends on the record you built.' },
        { id: 'settlement', label: 'Accept the service settlement', description: 'Take restored funding now and accept the office’s limited internal review.', effects: { care: 20, trust: 2, accountability: -15 }, consequence: 'The crew accepts the service agreement. Asha’s office retains control of the limited review.' },
        { id: 'our-side', label: 'Protect the coalition’s future', description: 'Demand a leadership change; exempt the incoming coalition’s wider donor accounts from review.', effects: { accountability: -30, trust: -12, care: -5 }, consequence: 'The crew backs a leadership change with an exemption for the incoming coalition’s donor accounts.' },
      ] },
      { id: 'open-windows', objective: 'Return to The Newsroom board for the six-month epilogue.', targetId: 'board', trigger: 'interact', dialogue: [
        { speaker: 'Yusuf', text: 'Six months. The shutter still sticks.' },
        { speaker: 'Aadi', text: 'Some things take longer than a speech.' },
        { speaker: 'Meera', text: 'Then open it. There is work to do.' },
      ] },
    ],
  },
];

/** These thresholds are authored narrative rules, not a model of actual political change. */
export function chooseEnding(metrics: CampaignMetrics, history: readonly StoryDecision[] = []): CampaignEnding {
  const finalDecision = [...history].reverse().find(entry => entry.chapterId === 'public-hearing' && entry.stageId === 'hearing-choice')?.choiceId;
  if (finalDecision === 'settlement') return {
    id: 'bargain', title: 'The Bargain',
    description: 'Asha remains in office under a service agreement. The clinic’s shelves are full again, but the internal review releases only a summary. Meera welcomes the deliveries. Kavya keeps a space on the board for the file still missing.',
  };
  if (finalDecision === 'our-side' || (finalDecision === undefined && metrics.accountability < 45)) return {
    id: 'different-chair', title: 'A Different Chair',
    description: 'Asha steps down and Samar’s coalition takes office. The new cabinet restores services but keeps its donor file sealed. Noor looks at the familiar locked drawer. You changed who holds power; the next edition must ask how they use it.',
  };
  if (metrics.trust < 45) return {
    id: 'broken-coalition', title: 'The Broken Coalition',
    description: 'The inquiry preserves the records, but the crew separates after the hearing. Tara opens another forum; Noor keeps publishing alone. A useful finding survives without a shared mandate. Devnagar’s future remains contested.',
  };
  if (metrics.accountability >= 75 && metrics.trust >= 65 && metrics.care >= 60) return {
    id: 'open-windows', title: 'Open Windows',
    description: 'The independent review publishes the approval trail. Asha resigns; an interim council restores clinic funding and opens its own accounts. Tara challenges its first decision in public. Six months later, the garage board has room for questions about the new government too.',
  };
  if (finalDecision === undefined && metrics.care >= 65) return {
    id: 'bargain', title: 'The Bargain',
    description: 'Asha remains in office under a service agreement. The clinic’s shelves are full again, but the internal review releases only a summary. Meera welcomes the deliveries. Kavya keeps a space on the board for the file still missing.',
  };
  return {
    id: 'unfinished-city', title: 'An Unfinished City',
    description: 'The hearing orders disclosure and a further review. No side can claim a complete victory. The crew has made a public record, and Devnagar has started asking harder questions. The next decision belongs to the city, not a headline.',
  };
}
