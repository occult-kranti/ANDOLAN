# Confluence army simulation in Rust

The `lanes` command takes a wave number and a number of simulation ticks. It lays out both armies on the original Confluence routes and reports where each unit would be after marching without opposition. This gives designers a reproducible way to compare composition, rank spacing, facing and arrival times on all three lanes. [Shared Rust rules and differential test](../../../yuga-rust/src/army.rs) · [Command-line driver](../../../yuga-rust/src/bin/lanes.rs) · [Canonical map](../../assets/world/confluence-map.json)

```sh
cargo run --locked --manifest-path games/yuga-rust/Cargo.toml --bin lanes -- 15 1200
```

The example asks for the fifteenth wave, 60 seconds into its march. Its event starts 420 seconds after reset. The JSON lists each unit's team, lane, role, lateral offset, progress in metres, world X/Z position, heading in radians and arrival tick. That wave has 12 spearmen, 12 bow guards, 6 commanders, 6 cannon carts and 2 royal chariots. Four central-lane spearmen have already arrived in that isolated projection. The Moon chariot is still on Temple avenue at approximately `[0, -85.8]`. Use `1 0` for the initial deployment, or `--help` for usage.

## Rules carried into Rust

| Native rule | Behavior in the executable |
| --- | --- |
| Wave ordering | Event 1 starts at reset. Events are spaced 600 ticks apart at 20 Hz. On each event, which lane gets the first formation rotates west → middle → east. Within a lane Sun deploys before Moon. |
| Infantry ranks | Each team on each lane gets two spearmen at 8 m, two bow guards at 5.4 m and a commander at 2.8 m. The paired ranks march at offsets −1.2 and +1.2 m. |
| Siege formations | Every third event adds one cannon cart per team on **each** lane at 5 m. Every fifth adds one royal chariot per team on the **middle** lane at 11.8 m. Both additions occur on wave 15. |
| Routes and movement | The map supplies the ordered 3D waypoints. Flat X/Z paths measure 269.295 m for Ghat promenade and Metro gardens and 224 m for Temple avenue. Moon samples the polyline in reverse and flips the lateral offset. At a bend the exact vertex belongs to the incoming segment. Each role uses its native speed and body radius, and arrives on the first tick within 0.05 m of the far end. |
| Static geometry | The Rust world tests each formation corridor against the 16 native blocking footprints with the appropriate clearance and checks radius-inset floor bounds. It also checks the short translation between offset ranks on adjacent segments and rejects a self-overlapping initial formation. A blocked corridor produces an error. |

The placement order, route direction, siege recurrence and arrival threshold come from the existing Godot army. Role speeds and radii come from its minion stats. [Native simulation](../../scripts/lane_army.gd) · [Native role data](../../scripts/lane_minion.gd) · [Rust ground queries](../../../yuga-rust/src/world.rs)

## Verification

```sh
cargo test --locked --manifest-path games/yuga-rust/Cargo.toml --lib army::tests
# Godot 4.6.3 with the native project's resources imported
cargo test --locked --manifest-path games/yuga-rust/Cargo.toml --lib army::tests -- --include-ignored
```

The ordinary tests reconstruct the original 30-unit formation, then check all 14 per-role census rows recorded for events 2–15. They check faction symmetry per lane, a flanking unit straddling a lateral bend, reverse headings and the first arrival tick for all 38 wave-15 marchers. The source record used a cleared-spawn fixture between events. [Siege QA record](../evidence/siege-qa/army-final.json) · [Native fixture](../../tests/siege_army_cases.gd) · [Initial 30-unit and timing record](../evidence/siege-qa/lane-army-regression-final.json)

The optional fourth test runs the current project in a separate Godot process. It compares all 136 native spawn rows from waves 1, 3, 5 and 15 against Rust, including per-role speeds, radii, headings, order and coordinates. It separately marches a single spearman along each lane from each end in Godot, compares sampled X/Z positions to within 1 mm and checks the exact arrival tick on all six journeys. All four tests passed on Godot 4.6.3 and Rust 1.88. Set the `GODOT_BIN` environment variable to select a different Godot executable. [Oracle and assertions](../../../yuga-rust/src/army.rs)

## Next match integration

The wave-number mode models one cleared wave at a time. Troops can pass through each other while marching, and reported arrivals mark route completion. The native match also tracks pressure across waves, target acquisition, attacks, body separation, deaths, rewards, core damage and winners. The isolated projection exercises spawn and movement independently of those systems. The existing native Godot match includes those behaviors. [Native lifecycle test](../../tests/lane_army_cases.gd)

The persistent mode now retains both armies between events, tracks both cores and admits formations atomically. Run the same command with `--match 24000` for 20 simulated minutes. The match guide reports its verification separately from the uncontested projections on this page. [Persistent match and source comparison](deep-search/ARMY-PORT.md) · [Original pressure and soak results](../evidence/siege-qa/army-final.json)
