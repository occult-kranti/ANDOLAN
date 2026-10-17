# Actual siege simulation — render r2

17 October 2026. Technical capture passed: 180 consecutive actual Forward+ frames at 1280 × 720, 360 advancing physics ticks, six simulated seconds, time scale 1. The silent MP4 decodes to 180 frames at 30/1. These are software-rendered frames, not measured realtime GPU performance.

The capture starts the public Siege practice drill once, stages one fixed camera, then records uninterrupted ordinary simulation. There are no per-frame actor/attack state writes. It starts with two cannon carts, two royal chariots and two spearmen. The event ledger records eight windups, eight impacts and thirteen affected-target hits; both spearmen are defeated. The four vehicles survive. All captured articulation remains finite and vehicles move. Current source hashes for 229 files and three validated GLB imports are retained in `siege-render-review.json`.

Root inspected frames 45 and 145; the art reviewer inspected frames 45 and 90. These retained frames show distinct vehicles, team colors and ground warnings without the initial camera obstruction. Source/export identity and packaging are separate release gates. The numerical/capture checks passed; detailed motion, final materials and commercial art quality remain unapproved.

The first camera take was rejected because its origin intersected architecture. The retained failure is in `../siege-render-r1-rejected/`. This take uses a corrected camera with actual collision-point and sight-ray clearance checks. All raw frames remain in `/workspace/scratch/yuga-siege/render-r2`; the full silent movie and three selected PNGs are archived here.

## Independent two-frame art review

Inspected the actual 1280 × 720 images `render-r2/frame-00045.png` and `render-r2/frame-00090.png` using the image viewer. This review accepts the revised framing as useful, unobstructed prototype evidence. It does not approve final art quality or the full 180-frame take, which was still running when these two frames were reviewed.

The earlier r1 camera-inside-building take is rejected separately at `docs/evidence/siege-render-r1-rejected`. In the two r2 frames, the battle is visible along the open lane; the left building occupies foreground space without covering the units or central warnings.

## Visible result

- **Vehicles:** The nearest cannon reads as a compact wheeled wood-and-brass gun carriage. The chariot ahead of it is taller and distinguished by its crown-framed backboard and standard. The opposing teal units are visibly separate from the rust/gold Sun group. Distant vehicle detail is small at this camera distance; the heavy bow and individual wheel spokes cannot be confidently judged from these frames.
- **Movement and contact:** Unit positions change between frames 45 and 90. No gross detached wheel, floating carriage, weapon-through-body intersection or building penetration is evident at this scale. This is a two-still observation, not approval of continuous wheel contact, recoil, cord alignment or death animation.
- **Warnings:** The gold and cyan circular areas are visible against the paving. Frame 90 shows several overlapping warnings around the central infantry, making individual boundaries and ownership harder to distinguish. A countdown, cancellation or exact impact moment cannot be validated from these two stills.
- **Staging:** The view provides useful positional context and keeps both teams in frame. Architecture fills much of the image, while the combat occupies a relatively narrow central region. A closer vehicle/impact view would be needed for detailed animation and art approval; the current framing remains suitable for a broad simulation demonstration.

## Remaining limits

The vehicles remain plainly procedural: broad flat materials, simplified mechanical silhouettes and little surface wear or sculpted ornament. Their material family fits the current infantry, but they do not meet the requested Deadlock/Overwatch visual target. Several map circles and combat warnings share bright ring shapes; dense overlap reduces warning clarity. No severe clipping defect is apparent in the inspected stills, but fine gripping, rotating-wheel and attack-phase details remain unreviewed.

The label correctly identifies a software render at a simulated playback rate. These images do not establish hardware frame rate, online multiplayer, audio quality or complete game readiness. No runtime, art or capture-helper changes were made during review.

## Source and image identity

The coordinator identifies the frozen runtime checkpoint as `9e8f54e`. Independently read byte hashes:

- `scripts/lane_vehicle_art.gd`: `c2962a3aab0bc6b6c819ef6fbdb77cad36e85a4066f2205f32d3b9748641aa2b`
- `tools/capture-siege.gd`: `b03c4b7e48f5683e9344d0a5863eb3929b30ac3d85dc51de66cfb2e22b7f33c1`
- `/workspace/scratch/yuga-siege/render-r2/frame-00045.png`: `b402e504d412d156aa10592a394c0163825fd789b582534258309a643e13e245`
- `/workspace/scratch/yuga-siege/render-r2/frame-00090.png`: `e21a8d076dd514e75d84f7539d766764bd141e2f6dce7ff2cb735f59d4e768a0`

A completed capture report, full media probe and exact source/export association remain separate release gates.
