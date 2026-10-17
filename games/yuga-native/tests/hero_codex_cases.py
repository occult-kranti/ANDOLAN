#!/usr/bin/env python3
"""Adversarial contracts for the design catalogue; no renderer required."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "games/yuga-native/tools/check-hero-codex.py"
spec = importlib.util.spec_from_file_location("hero_codex_validator", VALIDATOR)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def run():
    raw, base = checker.load_catalogue(checker.DEFAULT)
    browser = checker.browser_roster(str(ROOT))
    results = []

    def record(name, passed, detail=""):
        results.append({"name": name, "passed": bool(passed), "detail": detail})

    def reject(name, mutate, expected):
        candidate = copy.deepcopy(base)
        mutate(candidate)
        try:
            errors = checker.validate(candidate, ROOT, browser)
            record(name, any(expected in error for error in errors), "; ".join(errors[:3]))
        except Exception as exc:
            record(name, False, "Validator crashed instead of rejecting: " + repr(exc))

    def ability(data, hero=0, slot=2):
        return data["heroes"][hero]["abilities"][slot]

    def demo(data, hero=0, slot=2):
        return ability(data, hero, slot)["native_demo"]

    record("complete current catalogue accepted", not checker.validate(base, ROOT, browser))
    record("fourteen exact identities and six women retained",
           [h["id"] for h in base["heroes"]] == list(checker.HERO_IDS) and
           all(h in checker.HERO_IDS for h in ("sita", "draupadi", "subhadra", "hidimbi", "chitrangada", "ulupi")))
    record("42 slots and14 independent primary concepts",
           sum(len(h["abilities"]) for h in base["heroes"]) == 42 and
           len({h["primary"]["effect"] for h in base["heroes"]}) == 14)
    reject("missing hero", lambda d: d["heroes"].pop(), "exactly 14")
    reject("duplicate hero identity", lambda d: d["heroes"][1].update(id="rama"), "hero IDs/order")
    reject("unknown hero identity", lambda d: d["heroes"][0].update(id="unapproved"), "hero IDs/order")
    reject("array instead of hero identity", lambda d: d["heroes"][0].update(id=[]), "hero IDs/order")
    reject("role drift", lambda d: d["heroes"][0].update(role="Keeper"), "identity/role changed")
    reject("missing Q slot", lambda d: d["heroes"][0]["abilities"].pop(0), "three ability")
    reject("Q/E reorder", lambda d: d["heroes"][0]["abilities"].reverse(), "slots must")
    reject("duplicate ability identity", lambda d: ability(d).update(id="rama.q"), "invalid/duplicate stable ID")
    reject("duplicate effect identity", lambda d: demo(d).update(effect_id="rama.q.v1"), "invalid/duplicate effect ID")
    reject("missing primary", lambda d: d["heroes"][0].pop("primary"), "missing stable primary")
    reject("renamed browser skill", lambda d: ability(d).update(name="Copied power"), "ability baseline changed")
    reject("silent damage buff", lambda d: ability(d)["browser_baseline"].update(power=999), "ability baseline changed")
    reject("silent whole-hero health buff", lambda d: d["heroes"][0]["browser_baseline"].update(health=999), "browser baseline changed")
    reject("stale source hash", lambda d: d["source_contract"].update(browser_roster_sha256="0"*64), "source hash is stale")
    reject("arbitrary source path", lambda d: d["source_contract"].update(browser_roster_path="../../outside"), "fixed repository path")
    reject("incorrect coordinate convention", lambda d: d["units"].update(up_axis="+Z"), "coordinate/time units")
    reject("falsely accepted production art", lambda d: d["scope"].update(production_art_accepted=True), "design-only scope")
    reject("catalogue claims native damage authority", lambda d: demo(d).update(applies_gameplay=True), "presentation must not claim")
    reject("missing counterplay", lambda d: demo(d).update(counterplay=[]), "counter explanation")
    reject("blank primary counter", lambda d: d["heroes"][0]["primary"].update(counterplay=[" "]), "primary counterplay")
    reject("missing silhouette", lambda d: d["heroes"][0]["art_direction"].update(silhouette=""), "missing art silhouette")
    reject("missing materials", lambda d: d["heroes"][0]["art_direction"].update(materials=[]), "material separation")
    reject("duplicate signature shape", lambda d: demo(d,1).update(shape=demo(d)["shape"]), "unique signature shapes")
    reject("unknown effect family", lambda d: demo(d).update(family="execute_script"), "unknown effect family")
    reject("malformed effect family", lambda d: demo(d).update(family=[]), "unknown effect family")
    reject("projectile relabelled as summons", lambda d: demo(d).update(family="summon_pair"), "family contradicts baseline")
    reject("aimed projectile relabelled self-centred", lambda d: demo(d).update(anchor="caster"), "anchor contradicts baseline")
    reject("nonfinite effect radius", lambda d: demo(d).update(radius_m=float("nan")), "invalid radius_m")
    reject("huge valid JSON integer rejected without overflow", lambda d: demo(d).update(radius_m=10**400), "invalid radius_m")
    reject("infinite particle budget", lambda d: demo(d)["budget"].update(max_particles=float("inf")), "invalid resource budget")
    reject("bool masquerading as radius", lambda d: demo(d).update(radius_m=True), "invalid radius_m")
    reject("negative range", lambda d: demo(d).update(range_m=-1), "invalid range_m")
    reject("unbounded vertical spectacle", lambda d: demo(d).update(height_m=500), "invalid height_m")
    reject("zero-sized complete effect", lambda d: demo(d).update(range_m=0,radius_m=0,width_m=0,height_m=0), "invalid range_m")
    reject("footprint hidden by undersized width", lambda d: demo(d).update(width_m=.1), "declared diameter")
    reject("negative preparation", lambda d: demo(d)["timing"].update(windup_s=-.1), "invalid/nonfinite timing")
    reject("nonfinite preparation", lambda d: demo(d)["timing"].update(windup_s=float("nan")), "invalid/nonfinite timing")
    reject("payload before warning", lambda d: demo(d).update(payload_at_s=0), "payload must follow")
    reject("telegraph disagrees with release", lambda d: demo(d)["telegraph"].update(lead_s=.1), "telegraph timing disagrees")
    reject("bool masquerading as one-second warning", lambda d: demo(d)["telegraph"].update(lead_s=True), "telegraph timing disagrees")
    reject("zero-travel positive-range projectile", lambda d: (demo(d)["timing"].update(travel_s=0),demo(d).update(payload_at_s=1)), "projectile travel must")
    reject("unbounded nominal projectile speed", lambda d: (demo(d)["timing"].update(travel_s=.000001),demo(d).update(payload_at_s=1.000001)), "projectile travel must")
    reject("instant browser Q described as advance warning", lambda d: demo(d,0,0)["timing"].update(windup_s=.5), "cannot invent Q/E")
    reject("demo windup labelled as existing rule", lambda d: demo(d,1).update(timing_mode="browser_windup_preserved"), "misleading current/proposed")
    reject("Hanuman authoritative leap altered", lambda d: demo(d,4)["timing"].update(travel_s=.9), "existing leap travel changed")
    reject("Sita sanctuary extended", lambda d: demo(d,8)["timing"].update(active_s=8), "existing sanctuary duration changed")
    reject("effect pool overflow", lambda d: demo(d)["budget"].update(max_instances=10000), "resource budget max_instances")
    reject("light budget overflow", lambda d: demo(d)["budget"].update(max_lights=2), "resource budget max_lights")
    reject("draw budget overflow", lambda d: demo(d)["budget"].update(max_draw_calls=17), "resource budget max_draw_calls")
    reject("audio budget overflow", lambda d: demo(d)["budget"].update(max_audio_voices=4), "resource budget max_audio_voices")
    reject("triangle budget overflow", lambda d: demo(d)["budget"].update(max_triangles=999999), "resource budget max_triangles")
    reject("pool expires before choreography", lambda d: demo(d)["budget"].update(lifetime_s=.1), "budget expires")
    reject("unbounded lifetime", lambda d: demo(d)["budget"].update(lifetime_s=100), "budget expires")
    reject("global pool cap silently raised", lambda d: d["limits"].update(max_instances_per_cast=9999), "global resource cap")
    reject("bool masquerading as global light cap", lambda d: d["limits"].update(max_lights_per_cast=True), "global resource cap")
    reject("primary silently declared production accepted", lambda d: d["heroes"][0]["primary"].update(native_status="production_accepted"), "primary must retain proposal")
    reject("malformed palette colour", lambda d: d["heroes"][0]["art_direction"]["palette"].update(body="not-a-colour"), "palette identity drift")
    reject("baseline palette silently changed", lambda d: d["heroes"][0]["art_direction"]["palette"].update(accent="#000000"), "palette identity drift")
    reject("low quality drops warning", lambda d: demo(d)["telegraph"].update(retained_on_low_settings=False), "low settings must retain")
    reject("opaque centre hides targets", lambda d: demo(d)["telegraph"].update(maximum_centre_opacity=1), "readability opacity")
    reject("Rama gains phantom arrows", lambda d: demo(d).update(projectile_count=30), "projectile count")
    reject("Subhadra gains third summon", lambda d: demo(d,10).update(summon_count=3), "summon count")
    reject("Hidimbi gains permanent summons", lambda d: demo(d,11)["timing"].update(active_s=8), "summons must last nine")
    with tempfile.TemporaryDirectory(prefix="yuga-codex-negative-") as temp:
        path = Path(temp) / "bad.json"
        for label, content, expected in [
            ("duplicate JSON keys", b'{"schema_version":1,"schema_version":2}', "duplicate JSON key"),
            ("NaN JSON literal", b'{"x":NaN}', "nonfinite JSON"),
            ("Infinity JSON literal", b'{"x":Infinity}', "nonfinite JSON"),
            ("oversized file rejected before parsing", b' '*(checker.MAX_BYTES+1), "exceeds 2 MiB"),
        ]:
            path.write_bytes(content)
            try:
                checker.load_catalogue(path)
                record(label, False, "bad input accepted")
            except ValueError as exc:
                record(label, expected in str(exc), str(exc))
        path.write_bytes(raw)
        reread, parsed = checker.load_catalogue(path)
        record("valid JSON round trip retains catalogue", reread == raw and parsed == base)
    return {"passed": all(x["passed"] for x in results), "checks": len(results),
            "scope": "Real catalogue versus current TypeScript plus adversarial data/parser cases; no visual, performance or balance acceptance",
            "catalogue_sha256": hashlib.sha256(raw).hexdigest(),
            "validator_sha256": hashlib.sha256(VALIDATOR.read_bytes()).hexdigest(), "cases": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = run()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))
    if not report["passed"]:
        print(json.dumps([x for x in report["cases"] if not x["passed"]], indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
