"""Reconcile the aggregate inventories, optionally against prior independent local receipts."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_text())


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def verify(directory, local):
    checks = {}

    def equal(label, observed, expected):
        if observed != expected:
            raise ValueError(f"{label}: observed {observed!r}, expected {expected!r}")
        checks[label] = True

    source, nav, hanzo = (
        read_json(directory / name)
        for name in ("source.json", "nav.json", "hanzo.json")
    )
    props, source_mat, fan_mat = (
        read_csv(directory / name)
        for name in ("source-props.csv", "source-materials.csv", "hanzo-materials.csv")
    )

    def total(table, column):
        return sum(int(row[column]) for row in table)

    def class_counts(census):
        return {key: value["count"] for key, value in census["classes"].items()}

    for label, census in (
        ("Valve native", source["entities"]),
        ("Hanzo editable", hanzo["source_entities"]),
        ("Hanzo compiled", hanzo["compiled"]["entities"]),
    ):
        counts = class_counts(census)
        equal(label + " entity total", sum(counts.values()), census["count"])
        equal(label + " class total", len(counts), census["class_count"])

    native = source["records"]
    for column, count in (
        ("faces", "faces"),
        ("dispfaces", "dispinfo"),
        ("brushsides", "brushsides"),
        ("overlays", "overlays"),
        ("texture_info_slots", "texinfo"),
    ):
        equal("Valve per-material " + column, total(source_mat, column), native[count])
    equal("Valve material names", len(source_mat), source["materials_count"])
    equal(
        "Valve brush contents masks",
        sum(source["brush_content_masks"].values()),
        native["brushes"],
    )
    equal("Valve prop rows unique", len({r["native_model"] for r in props}), len(props))
    static = source["static_props"]
    equal("Valve prop paths", len(props), static["normalized_used_models"])
    equal("Valve prop placements", total(props, "placements"), static["placements"])
    equal(
        "Valve prop solidity",
        sum(static["placements_by_solidity"].values()),
        static["placements"],
    )
    locations = static["origin_families_by_nav_label"]
    equal(
        "Valve conservative prop location bins",
        sum(sum(r.values()) for r in locations.values()),
        static["placements"],
    )

    places = nav["places"]
    equal(
        "NAV area attributes", sum(nav["area_attribute_masks"].values()), nav["areas"]
    )
    equal(
        "NAV named places",
        len(places) - int("(unassigned)" in places),
        nav["declared_places"],
    )
    equal("NAV total areas", sum(r["areas"] for r in places.values()), nav["areas"])
    cross = sum(sum(r["links_out_to"].values()) for r in places.values())
    equal("NAV cross-place links", cross, nav["cross_label_links"])
    equal(
        "NAV all directed links",
        cross + sum(r["links_within"] for r in places.values()),
        nav["directed_links"],
    )
    equal(
        "NAV distinct ordered place pairs",
        sum(len(r["links_out_to"]) for r in places.values()),
        nav["directed_label_pairs"],
    )

    compiled = hanzo["compiled"]
    for column, count in (
        ("native_shader_slots", "base_shaders"),
        ("compiled_draw_surfaces", "draw_surfaces"),
        ("compiled_brushes", "collision_brushes"),
        ("compiled_brush_sides", "brush_sides"),
        ("jade_reassignments", "jade_changed_surfaces"),
    ):
        equal("Hanzo material " + column, total(fan_mat, column), compiled[count])
    equal(
        "Hanzo editable patches by shader",
        total(fan_mat, "source_patches"),
        hanzo["source_shapes"]["patches"],
    )
    for key, quantity in hanzo["source_shapes"].items():
        equal(
            "Hanzo source element ownership " + key,
            sum(row.get(key, 0) for row in hanzo["source_shapes_by_class"].values()),
            quantity,
        )
    equal(
        "Hanzo native draw types",
        sum(compiled["surface_counts_by_native_type"].values()),
        compiled["draw_surfaces"],
    )
    source_classes = class_counts(hanzo["source_entities"])
    removed = Counter(source_classes) - Counter(class_counts(compiled["entities"]))
    equal(
        "Hanzo source-only model placements",
        dict(removed),
        {"misc_model": sum(hanzo["external_model_references"].values())},
    )
    if local:
        evidence = local / "evidence"
        engine_inventory = read_json(evidence / "native-inventory.json")
        independent_ents = read_json(evidence / "source-entities.json")
        equal(
            "Earlier native class census",
            class_counts(source["entities"]),
            engine_inventory["entities"]["class_counts"],
        )
        equal(
            "Earlier independent entity list",
            dict(Counter(e["classname"] for e in independent_ents)),
            class_counts(source["entities"]),
        )
        equal(
            "Earlier native BSP identity",
            source["original_sha256"],
            engine_inventory["sha256"],
        )
        equal(
            "Earlier native records",
            {k: native[k] for k in engine_inventory["record_counts"]},
            engine_inventory["record_counts"],
        )
        old_static = engine_inventory["static_props"]
        equal(
            "Earlier native static placements",
            static["placements"],
            old_static["placements"],
        )
        equal(
            "Earlier native prop dictionaries",
            static["dictionary_slots"],
            old_static["dictionary_slots"],
        )
        diff = read_json(evidence / "native-diff.json")
        equal(
            "Earlier Valve jade identity", source["jade_sha256"], diff["variant_sha256"]
        )
        equal(
            "Earlier Valve changed face audit",
            source["jade"]["faces_reassigned_in_both_lighting_tables"],
            diff["changed_face_count"],
        )
        equal(
            "Earlier Valve stable lump count",
            source["jade"]["byte_identical_lumps"],
            diff["stable_lump_count"],
        )
        nav_csv = read_csv(evidence / "official-nav.csv")
        equal(
            "Earlier registered NAV area names",
            Counter(r["areaName"] or "(unassigned)" for r in nav_csv),
            Counter({k: r["areas"] for k, r in places.items()}),
        )
        equal(
            "Earlier distinct NAV IDs",
            len({r["areaId"] for r in nav_csv}),
            nav["areas"],
        )
        audit = read_json(local / "radiant/geometry-audit.json")
        equal(
            "Earlier Hanzo source identity",
            hanzo["source_map_sha256"],
            audit["source_map_sha256"],
        )
        equal(
            "Earlier Hanzo original BSP identity",
            compiled["original_bsp_sha256"],
            audit["base_sha256"],
        )
        equal(
            "Earlier Hanzo jade BSP identity",
            compiled["jade_bsp_sha256"],
            audit["jade_sha256"],
        )
        for key in (
            "draw_surfaces",
            "models",
            "vertices",
            "collision_brushes",
            "visibility_clusters",
        ):
            equal("Earlier Hanzo " + key, compiled[key], audit[key])
        changed = {
            "textures/" + r["material"]: int(r["jade_reassignments"])
            for r in fan_mat
            if int(r["jade_reassignments"])
        }
        equal(
            "Earlier Hanzo per-shader jade counts", changed, audit["changed_materials"]
        )
        equal(
            "Earlier Hanzo PK3 identities",
            {
                f"q3dust2-jb-beta6-{kind}.pk3": s
                for kind, s in hanzo["pack_sha256"].items()
            },
            audit["package_sha256"],
        )

    names = (
        "source.json",
        "nav.json",
        "hanzo.json",
        "source-props.csv",
        "source-materials.csv",
        "hanzo-materials.csv",
    )
    identities = {
        name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
        for name in names
    }
    return {
        "checked_earlier_local_evidence": local is not None,
        "checks": list(checks),
        "passed": len(checks),
        "published_sha256": identities,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory",
        default=HERE,
        type=Path,
        help="Directory containing the six inventory outputs",
    )
    parser.add_argument(
        "--local-package",
        type=Path,
        help="Compare against the earlier map-lab evidence as well",
    )
    parser.add_argument(
        "--record", type=Path, help="Write the deterministic result to this JSON file"
    )
    args = parser.parse_args()
    result = verify(args.directory, args.local_package)
    if args.record:
        args.record.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"{result['passed']} inventory reconciliations passed.")


if __name__ == "__main__":
    main()
