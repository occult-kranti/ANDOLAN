# ANDOLAN: City of Consequences

**Product:** a browser-native third-person city drama about a delivery crew, public services and the responsibilities that follow political change. Set in the invented river city of Devnagar, with an original cast, geography, dialogue and procedural visual kit.

**Current deliverable:** the *First Edition* development preview. Six condensed, playable chapters form one story with driving, walking, document discovery, seven consequential decisions, five possible epilogues and replay. The full 22-mission, six-to-ten-hour campaign remains a production goal. Preview duration has not been measured with first-time players.

## Player promise

Start at Yusuf’s garage, enter a car, discover why a clinic’s receipt disagrees with the public record, and carry the finding across a small inhabited district. Decide how Noor reports it, whether an ally deserves different rules, whose voices matter and what settlement the crew will accept. The story ends; the city’s problems do not disappear.

The investigation board is a destination in the city. Documents support the story without replacing movement, driving or character conversations. A government can change, reforms can occur without a change of government, or a new leadership can preserve old secrecy. These are authored fictional outcomes, not a simulation of real political organizing.

## Audience and supported tasks

- Players who want an accessible, story-led urban adventure they can open in a modern browser.
- Solo visitors who want to try the opening immediately.
- Invited crews who want a shared, server-owned story state and visible decisions.
- Developers and playtesters assessing the city feel, controls, continuity and networking before broader production.

## Visual and narrative direction

Warm workshop lights, muted mint facades, deep blue evening, coral mission markings and a distant river. The interface uses strong condensed titles and readable body text. The scene should feel like an authored city block, with the road and next task easy to read. No copied franchise map, radio, logo, character likeness or dialogue.

Characters retain the v0.3 handoff’s motives: Aadi wants the garage to survive, Noor wants her work to matter, Kavya learns that a proof needs an audience, and Meera insists services matter after the cameras leave. Allies have conflicts; opponents can make useful proposals. The player can make a wrong inference and correct it publicly.

## Release language

Use “development preview” and “six-chapter preview campaign.” Do not describe the preview as the entire open-world production or a public service ready for unrestricted use. Real connected clients, persistence, browser compatibility and performance require their own verification records. The interface must show the actual connection state; a local avatar is never presented as another real player.

## Acceptance gates

1. A visitor can walk, enter a car, drive to the clinic, exit and make the first decision.
2. Each chapter requires visiting at least two destinations and interacting with an authored scene.
3. Every document states both its source and what it does not establish.
4. Every decision has a clear description; effects persist and influence the epilogue.
5. An accepted settlement cannot produce an epilogue claiming an independent review.
6. The player can read the final outcome, review the decision history and deliberately replay.
7. The same server snapshot drives the task, dialogue, document board and shared crew outcome.

Content integrity is covered by `tests/content.test.ts`. Engine, networking and browser gate results belong in their actual validation reports, not inferred from the narrative specification.
