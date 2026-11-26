"""Share the Rust objective clock and surveyed movement rules across atlas consumers."""
import re

import audit


def rule_constants():
    source = audit.HERE.parents[4] / "yuga-rust" / "src" / "ritual.rs"
    expressions = dict(re.findall(r"pub const (\w+): (?:u32|f32) = ([^;]+);", source.read_text()))
    hz = int(expressions["HZ"])

    def ticks(key):
        match = re.fullmatch(r"(\d+) \* HZ(?: / (\d+))?", expressions[key])
        if not match:
            raise ValueError(f"Review changed Rust timing expression for {key}")
        return int(match[1]) * hz // int(match[2] or 1)

    return dict(hz=hz, approach=ticks("ROUND_TICKS"), kindle=ticks("IGNITE_TICKS"),
                quench=ticks("QUENCH_TICKS"), burn=ticks("BURN_TICKS"),
                reach=float(expressions["INTERACT_RANGE"]), siteRadius=audit.SITE_RADIUS,
                speed=audit.WALK_MPS, water=audit.WATER_FACTOR)
