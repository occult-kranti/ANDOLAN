# Independent implementation review — round 2

Date: 15 November 2026. Reviewer: tools/platform researcher. This is independent of the launch briefing implementation; the source helper is the reviewer's own earlier implementation and is therefore a self-review. No production code changed during this review.

## Decision

**No blocking briefing regression found in reviewed source or the additional eight headless checks. The three supplied compatibility-rendered native originals were directly reviewed; final combined-package input remains a separate render-owner gate.** The root's eleven-check contract report is supporting structural evidence, not image acceptance. The last inspected source hashes are below; later changes require checking their own receipt.

## Briefing / lifecycle / remapping

The new briefing uses the shared input-binding labels and canonical Rama glyph IDs. Mode changes update copy and diagram without starting play. The launcher refreshes bindings when returning to visibility; the actual settings host hides the launcher while remapping and restores its opener, while the launcher's deferred focus helper leaves an already-focused descendant alone. Loading keeps actions disabled, and the briefing introduces no interactive action. Relay copy agrees with the existing +3 arrows supply behavior in confluence_world.gd.

Additional actual Godot 4.6.3 headless checks passed **8/8**: pre-tree training selection; remapped Space/Shift/Ctrl labels at 1100x680, 1100x681, 1200x680, 1280x720 and 1920x1080; hide/show during loading with no disabled-action focus steal; queued deletion with focus released. All visible binding slots stayed inside the briefing and clear of the footer. Receipts are local `.local-tools/review/briefing-adversarial.json`; these tests do not establish pixels, human readability or OS input. The first review probe assumed a direct RamaBindings child, failed after the implementation nested it, and was corrected to find_child; the corrected probe passed without changing production code.

## Findings

| Severity | Finding | Evidence / action |
| --- | --- | --- |
| Medium, concept documentation | Generated native board displays incorrect bindings: Step Space, Guardian E and Volley Q, while actual native defaults are E/C/X. It also depicts piercing on a mouse button and invents ability effects such as invulnerability/target-area arrow rain. | Directly viewed yuga-native-screen-targets.png and compared input_bindings.gd / canonical ability labels. Root notified. Concept README must flag these errors and defer to runtime controls/specs. This is not a defect in launch_briefing.gd, which reads actual shared bindings. |
| Low, corrected by root: helper schema robustness | Initial version: catalog entries or install/license fields with wrong JSON types can raise AttributeError instead of the helper's structured JSON error. | load_catalog assumes each entry is a dictionary; selected_contract similarly assumes object-valued install/reuse/source and license rows. Existing curated catalog is valid and all seven current guard cases pass. Root added explicit object/array validation. The source-helper-hardening.json receipt passes eight adverse cases; reviewed correction at helper SHA c5546350e21e59d7404e8e754c5ce039c4bf310606794a89350fb00b3e78fbdb. No unsafe fetch was demonstrated. |
| Low, corrected by root: helper source completeness | Initial version: a typo in a non-license sparse path does not itself fail preparation. | Git sparse patterns permit nonexistent paths. The four actual prepared references were manually checked: every catalogued sparse path exists. Root added check_source_paths for new and existing checkouts and rejects a whole-root sparse dot; the eight-case hardening receipt includes missing-path rejection. Every actual catalogued source path exists. |

The helper correctly rejects the exercised non-HTTPS URL, symbolic ref, deferred/unknown IDs, dirty source and unreceipted existing directory, and verifies actual license hashes. Budget checks are after fetch/checkout phases plus a per-file cap; they are not a strict streaming total-download quota, already documented by the tool owner. No native provider/game client was run.

## Source identities

- `games/yuga-native/scripts/launch_shell.gd`: `9b1805d40fc11eecc21e86c23dab09cb38f4d0a79f48472b149ef63f0660ce36`
- `games/yuga-native/scripts/launch_briefing.gd`: `a2a6027e5e7f94fb37486b5b7fa144e1ce4ec6967a1b11fd4d35de3e0b181e94`
- `games/yuga-native/tests/launch_briefing_cases.gd`: `025bab9e1e6e775fdf3c126077e1179a5b0701f2bdcfc9b15abe85c1a5300810`
- `tools/research/prepare-open-source.py`: `a24f033bb1d3c990fd0c18779b17de667008457712964f0b995c4e1a8c77e1c7`
- `tools/research/opensource-catalog.json`: `fc72d484d7f94285ab29cd79ba729bceedfd57570c8698fe4a45482b1858405d`

Actual original compatibility-window captures were then directly opened: `docs/research/evidence/studio/briefing-confluence.png`, `briefing-training.png` and `briefing-guide.png`. Both titles show the selected practice, readable mode description, a dominant gold launch action, the matching schematic and actual LMB/Q/E/C/X keys. Footer/help/settings/quit remain visible and separate. The guide agrees with those bindings; no briefing clipping or overlap was observed at 1280×720. The guide's separate scrollable list/details are existing behavior, not a claim that every detail fits simultaneously. These originals support the scoped desktop composition; they do not establish all resolutions, hardware FPS or human playtest quality. The generated board remains a concept, not a native screenshot.

Image SHA-256 values:
- `briefing-confluence.png`: `4e36f17c69fb339104cffa80cb09edbe8557e6cc1cb2a3e0f57070151d9228bb`
- `briefing-training.png`: `be381390f6eb521742841893173fcc5cec714f4a3320794bf906d5d225f863aa`
- `briefing-guide.png`: `08f783e40f1501bbd75f02f8a715a18e808dc1cbc2d1d4c54e9ff139a6b24963`
