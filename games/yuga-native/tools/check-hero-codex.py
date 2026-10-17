#!/usr/bin/env python3
"""Validate the original hero design catalogue, not rendered/gameplay acceptance."""
import argparse
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
DEFAULT = ROOT / "games/yuga-native/assets/design/hero-codex.json"
MAX_BYTES = 2 * 1024 * 1024
HERO_IDS = ("rama", "ravana", "arjuna", "duryodhana", "hanuman", "karna", "bhima",
            "meghnad", "sita", "draupadi", "subhadra", "hidimbi", "chitrangada", "ulupi")
SHAPES = ("mirrored_arrow_eclipse", "ten_crown_iris", "horizon_needle", "iron_crescent_gate",
          "mountain_procession", "sunwheel_reversal", "fault_drum", "storm_scroll",
          "mithila_living_court", "fivefold_assembly", "twin_banner_procession",
          "walking_grove_pair", "crossing_oath", "naga_river_knot")
CAPS = {"max_instances": 48, "max_particles": 160, "max_lights": 1,
        "max_audio_voices": 3, "max_draw_calls": 16, "max_triangles": 18000}
KINDS = {"projectile", "forward_fan", "forward_cone", "radial", "protection",
         "restoration", "movement", "ground_zone", "ground_pull", "summon_pair"}
FAMILIES = {"bolt": "projectile", "line": "projectile", "burst": "forward_fan",
            "cone": "forward_cone", "nova": "radial", "ward": "protection",
            "heal": "restoration", "dash": "movement", "leap": "movement",
            "slow": "ground_zone", "pull": "ground_pull", "summon": "summon_pair"}
SOURCE_PATHS = {"browser_roster": "games/yuga/shared/heroes.ts",
                "simulation": "games/yuga/shared/simulation.ts",
                "design_master": "games/yuga-native/docs/GAME_DESIGN_MASTER.md"}


def reject_constant(value):
    raise ValueError("nonfinite JSON number: " + value)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def load_catalogue(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("catalogue exceeds 2 MiB")
    return raw, json.loads(raw, parse_constant=reject_constant, object_pairs_hook=unique_object)


@lru_cache(maxsize=4)
def browser_roster(root_string):
    # Fixed repository import, never executable code supplied by the catalogue.
    command = ["node", "--import", "tsx", "--input-type=module", "-e",
               "import { HEROES } from './games/yuga/shared/heroes.ts'; "
               "process.stdout.write(JSON.stringify(HEROES));"]
    completed = subprocess.run(command, cwd=root_string, capture_output=True, text=True,
                               timeout=20, check=True)
    return json.loads(completed.stdout)


def validate(data, root=ROOT, baseline=None):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def words(value):
        return isinstance(value, str) and bool(value.strip()) and len(value) <= 16384

    def number(value, minimum, maximum):
        # Bound arbitrary-precision JSON integers before any float conversion.
        return type(value) in (int, float) and minimum <= value <= maximum and (
            type(value) is int or math.isfinite(value))

    def text_list(value, minimum=1):
        return isinstance(value, list) and len(value) >= minimum and all(words(x) for x in value)

    def tree(value, depth=0):
        if depth > 32:
            errors.append("catalogue nesting exceeds 32")
            return
        if isinstance(value, float) and not math.isfinite(value):
            errors.append("nonfinite value anywhere in catalogue")
        elif isinstance(value, dict):
            for item in value.values():
                tree(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > 500:
                errors.append("oversized catalogue array")
                return
            for item in value:
                tree(item, depth + 1)

    if not isinstance(data, dict):
        return ["catalogue must be an object"]
    tree(data)
    require(type(data.get("schema_version")) is int and data["schema_version"] == 1, "schema_version must be 1")
    require(data.get("catalogue_id") == "yuga.hero_codex", "unknown catalogue_id")
    require(type(data.get("revision")) is int and data["revision"] >= 1, "revision must be a positive integer")
    units = data.get("units", {})
    require(isinstance(units, dict) and all(units.get(k) == v for k, v in
            {"distance": "metres", "time": "seconds", "up_axis": "+Y", "forward_axis": "+Z"}.items()),
            "coordinate/time units differ from the native contract")
    scope = data.get("scope", {})
    for field in ("browser_rules_changed", "native_hero_roster_implemented",
                  "native_practice_demonstrations_implemented", "production_art_accepted"):
        require(isinstance(scope, dict) and scope.get(field) is False,
                "design-only scope must keep " + field + " false")
    require(isinstance(scope, dict) and words(scope.get("timing_warning")), "missing current/proposed timing warning")
    sources = data.get("source_contract", {})
    for key, expected_path in SOURCE_PATHS.items():
        require(isinstance(sources, dict) and sources.get(key + "_path") == expected_path,
                key + " source must use the fixed repository path")
        actual = root / expected_path
        if not actual.is_file():
            errors.append("source missing: " + expected_path)
        else:
            require(isinstance(sources, dict) and sources.get(key + "_sha256") ==
                    hashlib.sha256(actual.read_bytes()).hexdigest(), key + " source hash is stale")
    limits = data.get("limits", {})
    for key, expected in {"heroes": 14, "ability_slots": 42, "primary_entries": 14,
                          "max_concurrent_demo_casts": 4, "max_effect_lifetime_s": 12.0}.items():
        require(isinstance(limits, dict) and type(limits.get(key)) in (int, float) and
                limits[key] == expected, "unexpected global limit " + key)
    for key, cap in CAPS.items():
        require(isinstance(limits, dict) and type(limits.get(key + "_per_cast")) is int and
                limits[key + "_per_cast"] == cap,
                "unexpected global resource cap " + key)
    require(isinstance(limits, dict) and words(limits.get("hardware_status")), "missing provisional hardware limit")
    heroes = data.get("heroes")
    if not isinstance(heroes, list) or len(heroes) != 14 or not all(isinstance(h, dict) for h in heroes):
        return errors + ["heroes must contain exactly 14 objects"]
    require([h.get("id") for h in heroes] == list(HERO_IDS), "hero IDs/order must preserve the complete browser roster")
    if baseline is None:
        try:
            baseline = browser_roster(str(root))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            return errors + ["cannot inspect current browser roster; run npm ci: " + str(exc)]
    by_id = {h["id"]: h for h in baseline}
    all_ids, effect_ids, ultimate_shapes = set(), set(), []
    for hero in heroes:
        ident = hero.get("id")
        if not isinstance(ident, str) or ident not in by_id:
            continue
        expected = by_id[ident]
        require(hero.get("browser_baseline") == expected, ident + ": browser baseline changed")
        require(hero.get("name") == expected["name"] and hero.get("role") == expected["role"], ident + ": identity/role changed")
        require(hero.get("source_motif") in ("R1", "M1"), ident + ": unknown source motif")
        art = hero.get("art_direction", {})
        for field in ("title", "silhouette", "motion_language", "production_risk", "concept_prompt"):
            require(isinstance(art, dict) and words(art.get(field)), ident + ": missing art " + field)
        require(isinstance(art, dict) and text_list(art.get("materials"), 3), ident + ": missing material separation")
        palette = art.get("palette", {}) if isinstance(art, dict) else {}
        require(isinstance(palette, dict) and words(palette.get("team_marker")), ident + ": missing separate team marker")
        for field, expected_color in (("body", expected["color"]), ("accent", expected["accent"])):
            value = palette.get(field) if isinstance(palette, dict) else None
            require(isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value) is not None and
                    value == expected_color, ident + ": invalid/palette identity drift " + field)
        primary = hero.get("primary", {})
        require(isinstance(primary, dict) and primary.get("id") == ident + ".primary" and
                primary.get("slot") == "PRIMARY", ident + ": missing stable primary")
        for field in ("effect", "telegraph", "motion"):
            require(isinstance(primary, dict) and words(primary.get(field)), ident + ": missing primary " + field)
        require(isinstance(primary, dict) and text_list(primary.get("counterplay")), ident + ": missing primary counterplay")
        require(isinstance(primary, dict) and primary.get("native_status") == "presentation_proposal",
                ident + ": primary must retain proposal scope")
        abilities = hero.get("abilities")
        if not isinstance(abilities, list) or len(abilities) != 3 or not all(isinstance(x, dict) for x in abilities):
            errors.append(ident + ": exactly three ability objects required")
            continue
        require([a.get("slot") for a in abilities] == ["Q", "E", "R"], ident + ": slots must be Q/E/R")
        for index, ability in enumerate(abilities):
            slot = ("q", "e", "r")[index]
            aid = ident + "." + slot
            require(ability.get("id") == aid and aid not in all_ids, aid + ": invalid/duplicate stable ID")
            all_ids.add(aid)
            base = expected["abilities"][index]
            require(ability.get("browser_baseline") == base and ability.get("name") == base["name"], aid + ": ability baseline changed")
            require(words(ability.get("effect")) and text_list(ability.get("counterplay")), aid + ": missing effect/counterplay")
            require(words(ability.get("change_policy")), aid + ": missing rule migration boundary")
            demo = ability.get("native_demo")
            if not isinstance(demo, dict):
                errors.append(aid + ": missing native_demo")
                continue
            eid = demo.get("effect_id")
            require(eid == aid + ".v1" and eid not in effect_ids, aid + ": invalid/duplicate effect ID")
            if isinstance(eid, str):
                effect_ids.add(eid)
            require(isinstance(demo.get("family"), str) and demo["family"] in KINDS, aid + ": unknown effect family")
            require(demo.get("family") == FAMILIES[base["kind"]], aid + ": effect family contradicts baseline")
            require(words(demo.get("shape")), aid + ": missing shape")
            if slot == "r":
                ultimate_shapes.append(demo.get("shape"))
            require(demo.get("anchor") in ("caster", "aimed_forward", "aimed_ground"), aid + ": invalid anchor")
            expected_anchor = "aimed_ground" if base["kind"] in {"slow", "pull"} or base.get("mechanic") == "mountain-descent" else (
                "aimed_forward" if base["kind"] in {"bolt", "line", "burst", "cone", "dash", "leap"} else "caster")
            require(demo.get("anchor") == expected_anchor, aid + ": effect anchor contradicts baseline")
            for field, cap in {"range_m": 32, "radius_m": 10, "width_m": 24, "height_m": 10}.items():
                require(number(demo.get(field), .001, cap), aid + ": invalid " + field)
            if number(demo.get("radius_m"), .001, 10) and number(demo.get("width_m"), .001, 24):
                require(demo["width_m"] >= 2 * demo["radius_m"], aid + ": width cannot hide the declared diameter")
            require(demo.get("applies_gameplay") is False, aid + ": presentation must not claim gameplay authority")
            for field in ("collision_policy", "low_quality", "reduced_motion", "audio_cue"):
                require(words(demo.get(field)), aid + ": missing " + field)
            require(text_list(demo.get("counterplay")), aid + ": missing executable counter explanation")
            times = demo.get("timing", {})
            valid_time = isinstance(times, dict) and all(number(times.get(k), 0, cap) for k, cap in
                {"windup_s": 2, "travel_s": 2, "active_s": 9, "recovery_s": 2}.items())
            require(valid_time, aid + ": invalid/nonfinite timing")
            if not valid_time:
                continue
            total = sum(times.values()) if set(times) == {"windup_s", "travel_s", "active_s", "recovery_s"} else -1
            require(0 < total <= 12, aid + ": invalid complete lifetime")
            require(number(demo.get("payload_at_s"), 0, 12) and
                    abs(demo["payload_at_s"] - times["windup_s"] - times["travel_s"]) <= .001,
                    aid + ": payload must follow preparation and travel")
            if base["kind"] in {"bolt", "line"}:
                travel = times["travel_s"]
                valid_range = number(demo.get("range_m"), .001, 32)
                require(travel > 0 and valid_range and number(demo["range_m"] / travel, 20, 80),
                        aid + ": projectile travel must be positive with bounded nominal speed")
            if base["kind"] in {"dash", "leap"}:
                require(times["travel_s"] > 0, aid + ": movement choreography requires travel time")
            expected_mode = "browser_windup_preserved" if base.get("mechanic") else (
                "proposed_native_demo_windup" if slot == "r" else "immediate_browser_presentation")
            require(demo.get("timing_mode") == expected_mode, aid + ": misleading current/proposed timing mode")
            if base.get("mechanic"):
                require(times["windup_s"] == base["windup"], aid + ": existing special windup changed")
                if ident == "hanuman":
                    require(times["travel_s"] == .45, aid + ": existing leap travel changed")
                if ident == "sita":
                    require(times["active_s"] == 6, aid + ": existing sanctuary duration changed")
            elif slot == "r":
                require(times["windup_s"] >= .35, aid + ": proposed R warning too short")
            else:
                require(times["windup_s"] == 0, aid + ": cannot invent Q/E advance warning")
            telegraph = demo.get("telegraph", {})
            expected_kind = "advance_warning" if times["windup_s"] > 0 else "release_or_aftermath"
            require(isinstance(telegraph, dict) and telegraph.get("kind") == expected_kind and
                    number(telegraph.get("lead_s"), 0, 2) and telegraph["lead_s"] == times["windup_s"],
                    aid + ": telegraph timing disagrees")
            require(isinstance(telegraph, dict) and telegraph.get("retained_on_low_settings") is True and
                    words(telegraph.get("shape")), aid + ": low settings must retain boundary")
            require(isinstance(telegraph, dict) and number(telegraph.get("maximum_centre_opacity"), 0, .25) and
                    number(telegraph.get("minimum_visible_opacity"), .15, 1), aid + ": invalid readability opacity")
            resource = demo.get("budget", {})
            for field, cap in CAPS.items():
                minimum = 1 if field in {"max_instances", "max_draw_calls", "max_triangles"} else 0
                require(isinstance(resource, dict) and type(resource.get(field)) is int and
                        minimum <= resource[field] <= cap, aid + ": invalid resource budget " + field)
            require(isinstance(resource, dict) and number(resource.get("lifetime_s"), max(0, total), 12),
                    aid + ": budget expires before choreography or exceeds cap")
            expected_projectiles = 3 if base.get("mechanic") == "dawn-volley" else (1 if base["kind"] in {"bolt", "line"} else 0)
            require(type(demo.get("projectile_count")) is int and demo["projectile_count"] == expected_projectiles,
                    aid + ": projectile count misrepresents baseline")
            require(type(demo.get("summon_count")) is int and demo["summon_count"] == (2 if base["kind"] == "summon" else 0),
                    aid + ": summon count misrepresents baseline")
            if base["kind"] == "summon":
                require(times["active_s"] == 9, aid + ": temporary summons must last nine seconds")
    require(len(all_ids) == 42 and len(effect_ids) == 42, "catalogue must contain all 42 stable ability/effect IDs")
    require(ultimate_shapes == list(SHAPES), "fourteen unique signature shapes must retain their hero mapping")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", type=Path, default=DEFAULT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        raw, data = load_catalogue(args.codex)
        errors = validate(data)
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        raw, errors = b"", [str(exc)]
    report = {"passed": not errors, "scope": "Catalogue/source compatibility, complete IDs, safe numeric bounds and design contracts only; not rendered art, balance or native gameplay acceptance",
              "catalogue_sha256": hashlib.sha256(raw).hexdigest(), "heroes": 14 if not errors else None,
              "ability_slots": 42 if not errors else None, "errors": errors}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
