# Historical film fixture archive repair

CI39085923559 stopped in evidence validation because two historical QA manifests pinned the mutable current `tests/combat_film_cases.gd` path. The current fixture now waits on real elapsed loading time; its old bytes remain exactly SHA256 `94f64f91bbaa50d57cacbaff471d286448e5c016630b2c69945ad5894cb7b4d2`,27906 bytes, recovered from committed00a204b.

Both manifest paths now name that archived exact fixture under `tests/evidence/combat-film-legacy-fixture/`, retaining original source path, digest and size. No old result is attributed to the new fixture; the current42-case run remains separate. The evidence checker is unchanged.
