# Rama confirmed-contact family

Task `RAMA-COMPLETE-01`, combat/audio owner. Native desktop/offline Rama.
Baseline commit `7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch
`work/yuga-studio`, preserving existing uncommitted hero, UI and world work.

This implementation improves the physical meaning of projectile feedback.
The old effects consumer made a strong hit bloom for every `reason == unit`,
even with no positive damage receipt, and made a physical-looking bloom at an
empty maximum-range endpoint. A higher-sequence repeat could also repeat the
same target contact. The audio consumer already required positive damage;
visual and sound feedback now use the same pure receipt classifier.

## Implemented contract

`rama_hit_response.gd` is presentation-only. `classify(receipt)` returns
`health`, `shield` or `defeat` only when all four receiver snapshot fields are
finite, nonnegative, nonincreasing and reconcile with effective damage.
`defeat` specifically requires positive health before and zero health after.
Older positive-only receipts remain generic `contact`; missing/partial or
inconsistent snapshots never invent a typed defeat. Zero damage is silent.
The helper never applies damage, awards currency or changes an authority clock.

| Actual outcome | World presentation | Existing audio presentation |
| --- | --- | --- |
| Health loss | Existing fine warm-gold contact quills | Existing contact/confirmation at ordinary bounded pitch |
| Shield-only loss | Open cool-teal fractured facets | Existing dull spatial contact and lower local confirmation pitch |
| Confirmed defeat | Small open six-petal solar signature | Existing contact/confirmation at higher bounded pitch |
| Solid wall | Restrained copper/dull sparks | Existing blocked cue; no success confirmation |
| Empty maximum range, empty/zero/inconsistent receipt | No physical contact or success bloom | No success confirmation |

Each cast deduplicates target/projectile contacts. A terminal projectile replay
is rejected before cast clocks, last-event data or the event watermark change.
The original power warnings, action admissions, release cadence, collision,
damage, cooldown and rewards are untouched.

Contact geometry reuses the same 18-node pool and at most eight immutable
normal/reduced meshes. Each style stays at or below312 triangles; the dense
18-contact case remains at or below5,616 triangles, with zero lights and zero
particles. Reduced effects keep the distinguishing open silhouette, while
reduced motion keeps its transform stationary. Existing warning geometry and
per-pulse retirement are unchanged.

No audio files or shared manifests changed. The same15 original streams,
three spatial players and one local feedback player are retained. The fixed
response pitch multipliers are0.88 for shield,1.0 for ordinary contact and1.18
for defeat, in addition to the existing small deterministic variation. A newly
confirmed defeat may strengthen an ordinary confirmation in the same short
coalescing window. Incoming danger keeps its higher priority and cannot be
evicted by a hit/defeat confirmation. No bus changes, extra players, delayed
onset queues or external recordings were introduced.

## Executed verification

| Suite | Final result |
| --- | --- |
| New actual receiver/contact/audio counterexamples | 52/52 |
| Existing effects geometry/resources | 74/74 |
| Existing audio schema/voices/lifecycle | 115/115 |
| Existing independent effects adversarial suite | 57/57 |

All four selected runs exit0 with no warnings/errors. Exact commands, hashes
and source-bound reports are in [receipt.json](receipt.json) and `reports/`.
These headless/Dummy-driver results establish receipt selection, geometry,
pooling and lifecycle. They do not establish human listening, actual rendered
readability, control feel, physical-GPU performance or complete hero art.

The existing adversarial pool fixture had treated its first Piercing impact as
an actual contact, but it was only range expiry. Its initial54/56 failure is
retained. The corrected fixture stages one actual Moon receiver before the
cast, then explicitly requires `unit` plus positive damage before exercising
the unchanged pooling/expiry assertions. Numeric budgets were not relaxed.
The new suite separately verifies no contact at empty maximum range.

The new harness initially freed consumers before the kit, which emits cancel
on exit; that caused a teardown crash despite its assertions passing. That run
is rejected and retained. Kit teardown now happens while subscribers are alive,
then it stops audio and waits up to one second for actual Dummy playback weak
references to retire. A transient exit warning and its diagnostic run are also
retained. Final52/52 exits cleanly.

## Native capture handoff

Root owns imports, integration and the heavy render lane. The new helper still
needs its normal generated UID through the root-owned import before export.
For actual native world casts, stage live receiver positions before calling the
real world cast entry; retain original muzzle sampling and the normal army clock:

1. Kodanda versus150 health/no shield produces `health`.
2. Kodanda versus150 health with an actual45-shield/12-second grant produces `shield`.
3. Kodanda versus20 health/no shield produces `defeat`.
4. A real solid wall before the receiver produces `wall` without success.
5. A clear empty40m lane produces no physical contact bloom.

Record the first0.42 seconds of actual contact at30Hz, reading
`effects.report().contact_styles` and `action_audio.report().last_contact` /
voice `response` metadata alongside images. Inspect at useful gameplay scale
and a clear three-quarter contact angle, plus reduced-effects/motion flags.
The usual healthy-target five-action film alone will not demonstrate the new
shield and defeat variants. The fixture must state its staged receiver setup;
it must not be described as a human match or auditory approval.

Root's courtyard integration now retains real hit/defeat counters while retiring
the old duplicate HIT/TARGET CLEARED popup/ring/audio when the configured Rama
runtime owns the shot. New UI reticle feedback belongs to the UI owner; this
owner adds no competing UI hitmarker or camera kick.

Next owners: root imports/renders/packages the composed hero; independent UI/art
review decides actual visual acceptance. Audio/game designer performs named
listening and combat-feel review. No external art/code/audio was copied here;
all new geometry/classification code is original and existing source notices
continue to apply.
