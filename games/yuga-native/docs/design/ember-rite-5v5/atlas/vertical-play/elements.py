"""Publish the surveyed height and interaction register from the 53 art subjects."""

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parents[4] / "art/mandala-map-studio"
ROOM = {
    "atk": "Carry starts on the gate floor. Rehearse the two near-side staging routes before committing the vessel. The awning cannot catch a leap.",
    "def": "From the water gate, split the ewer escort and site scout. Gate roofs give no listening position over the preparation boundary.",
    "a": "Keep the inner 3 m kindle disk and 4.5 m approach apron open. Gada recovery uses ground outside the apron. A retaker can pour from beside an edge plant.",
    "b": "Distinguish the counter from the cabinet before entering. Its north and south pyramid mouths demand separate protection. Return discs can be interrupted by a cabinet.",
    "mid": "Raised crossing with a gearbox, two falling approaches and exposed shoulders. Read the landing edge before committing a lift. The gearbox is a solid.",
    "steps_s": "Let the carrier choose the dry rise or the shallow ford; a grounded escort can remain at the split. A rising arrow still needs a legal clear segment.",
    "steps_n": "Mark the jar-step fork before taking the wet approach. A defender can exchange the ewer on the dry approach; jars are wayfinding only.",
    "bank": "The bank floor rises 1.8 m above datum. Its parapet screens the lower silhouette. A model on the parapet art gets no extra jump surface.",
    "ford": "A shallow-water floor gives feet a place to land. Wading changes route time. No submerged hiding volume or current-driven drift is registered.",
    "temple_s": "A single V identifies the southern fold. Face the destination before using it. An ally can take the ordinary arcade for a different timing.",
    "pyramid_s": "The pavilion sits over a playable central bay. Read 5 m between the cheeks and 4.23 m to the lowest beam; a high cast meets masonry.",
    "temple_n": "Two bars identify the northern fold. Call the turn to the receiver before an ally takes it. The passage blocks a continuous projectile path.",
    "pyramid_n": "This exit has its own signed heading and a physical path into B. Confirm the exit is clear before committing a second hero.",
    "yard_s": "The southern cloth court feeds the dry pyramid approach. Drapes and hanging cloth provide no hard collision or airborne foothold.",
    "yard_n": "The scale court is the northern staging partner. Re-form here before the narrow pyramid entry. Scales supply a landmark rather than a firing platform.",
}
ROUTES = [
    "The west fork gives the ember carrier a dry or wet choice at its far end. Awnings above the line grant no extra floor.",
    "Keep an escort close until the temple fork. Preparation clips this approach at the team curtain.",
    "Cloth Yard is the eastern assembly route. Use ground pace for the opening comparison.",
    "The northern bank approach separates the retake caller from the ewer escort at Jar Steps.",
    "The temple path is the defending side’s first choice between arcade and fold.",
    "The scale-court path reaches the northern B approach. The scale landmark gives the lead player a repeatable facing cue.",
    "Rising floor shortens local overhead clearance. Measure a shot from the interpolated floor under the caster.",
    "The northern dry rise feeds the same bank. Compare two eyes at world elevation before calling the parapet full cover.",
    "The southern water branch trades pace for another arrival direction. An airborne handoff never lights the vessel.",
    "Shallow water on the northern approach keeps a real floor. Cloth and reeds do not shorten the water traversal.",
    "The last wet leg meets a raised dry bank. Commit a landing only where a support surface catches the full body.",
    "A seven-metre bank mouth feeds A from the west. Test the near recess and its separated alternate against the bank-height observer.",
    "A seven-metre southern sill faces into A. The first hero can cross while a second holds a different shelter.",
    "The northern seven-metre sill reverses the exposed sides of the furniture. Re-evaluate a southern hide before a retake.",
    "B’s south mouth is six metres wide. Hide behind a full-height block before exposing the carrier on the open apron.",
    "B’s north mouth is six metres wide. Dodge a visible departure and recheck hard masonry on the chakra return.",
    "A physical south connector reaches the pavilion before B. A high arc can strike the lintel instead of the ground target.",
    "The northern connector delivers players to the paired-mark doorway. Only rock with a registered solid stops a cast.",
    "The south arcade walks around the seam. A hero can pressure its physical bend while a teammate takes the marked fold.",
    "The north arcade provides a visible, continuous alternative to the paired bars. Its bends still occlude lines.",
    "One signed quarter turn transfers the hero locally. End a projectile at a seam; do not trace a straight line between the two room centres.",
    "The inverse direction restores the original frame. A follow-up ally uses the same sign, with a separate clearance check.",
    "The southern ramp climbs to central water control. Higher ground can expose a head hidden from a level doorway.",
    "The northern ramp approaches the same gearbox from the opposite side. Its legal standing footprint stays on the ramp.",
    "The narrow five-metre ramp enters A obliquely. Confirm both signed hiding places from the actual Sluice observer.",
    "The corresponding five-metre ramp enters B from the west. Treat it as a third entrance despite its shallow angle.",
]
PROPS = {
    "cover-bell-screen": "Full-height site solid. A rounded shoulder is still exposed at its edge. Compare against both the forward and reverse witnesses.",
    "cover-stone-lectern": "A 1.05 m leg screen. A standing eye and a 1.32 m crouched silhouette clear the top. Keep it as partial cover.",
    "cover-dye-cabinet": "Full-height east-site cabinet. Stops a swept projectile on contact. A high departure can see over it from some positions.",
    "cover-weigh-counter": "A 1.0 m market counter. The beam above is separate ornamental geometry. Never join their bounds into a full cover wall.",
    "cover-bank-parapet": "Mount the path to reach this base at +1.8 m. Compare receiver height against the parapet top in world metres.",
    "cover-sluice-gearbox": "A solid on the +1.4 m crossing. A rising or descending cast must clear both its footprint and top.",
    "artifact-bell-comb": "Three ribs point towards A. Use their distinctive rhythm as an approach cue. Only the separately registered Bell screen supplies certified cover.",
    "artifact-fold-lintels": "Four signs mark two fold pairs. Their 5 m-wide by 2.98 m-high art opening identifies the sign. Hero transfer uses the local seam volume and surveyed game geometry.",
    "artifact-weighbeam": "The arm points toward the B–Sluice route. It is a directional marker without a projectile-solid registration.",
    "architecture-quarter-turn-pavilion": "The 10 × 8 × 9 m assembly has 62 built pieces. The central passage is 5 m wide and 4.23 m high. Test the side piers and overhead courses separately from the bay.",
    "rite-ember-vessel": "Carry, drop and ground the vessel. Site disk applies to kindle, and the actual grounded position anchors the later 1.5 m pour reach.",
    "rite-water-ewer": "Role prop for the defender. One eligible grounded toucher channels the pour. Its painted spout supplies no extra interaction or projectile reach.",
}


def number(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def interval(a, b):
    return number(a) if abs(a - b) < 0.005 else f"{number(a)} to {number(b)}"


def render():
    catalog = json.loads((STUDIO / "catalog.json").read_text())["elements"]
    models = json.loads((STUDIO / "models/index.json").read_text())["models"]
    assert {v["id"] for v in catalog} == set(models)
    route_ids = [v["id"] for v in catalog if v["kind"] == "route"]
    assert len(route_ids) == len(ROUTES)
    route_rules = dict(zip(route_ids, ROUTES))
    lines = [
        "# Mandala Rift · height and interaction register",
        "",
        "All 53 subjects in the art library have a row below. The first height column is the ground or route datum in metres. The second is the lowest and highest visible vertex of the exported subject in world coordinates. A floor is walkable through its registered footprint. Decorative relief, overhangs and finials do not create extra landing surfaces. Solid site furniture uses the gameplay dimensions on the cover plans. Heights of equipped heroes and their gameplay receivers are documented separately. [Hero measurements](hero-abilities.md) · [Model index](../../../../../art/mandala-map-studio/models/index.json) · [Element gallery](https://occult-kranti.github.io/ANDOLAN/production/mandala-art/)",
        "",
        "The art exports use glTF Y-up. For each subject the world art limit equals the Blender registration elevation plus its local glTF Y limit. Floor and route elevations come from the district catalog. Local horizontal coordinates are east and north. A discontinuous fold has two physical ends and no floor spanning their gap.",
        "",
    ]
    for title, kinds in (
        ("Floors, preparation and sites", ("room",)),
        ("Connectors, gradients and folds", ("route",)),
        (
            "Cover, landmarks, pavilion and ritual objects",
            ("cover", "artifact", "architecture", "rite"),
        ),
    ):
        lines += [
            "## " + title,
            "",
            "| Subject | Floor / route elevation (m) | Art low to high (m) | Footprint or clear width | Interaction and counter |",
            "|---|---:|---:|---|---|",
        ]
        for e in catalog:
            kind = e["kind"]
            id = e["id"]
            if kind not in kinds:
                continue
            mesh = models[id]
            base = mesh["origin_map_xyz_m"][2]
            bound = mesh["bounds_local_gltf_m"]
            art = interval(base + bound[0][1], base + bound[1][1])
            dim = e.get("size_m")
            if kind == "room":
                ground = number(e["floor_m"])
                size = " × ".join(map(number, dim)) + " m"
                rule = ROOM[e["source_key"]]
            elif kind == "route":
                h = [p[2] for p in e["points_xyz"]]
                ground = interval(min(h), max(h))
                size = number(e["width_m"]) + " m"
                rule = route_rules[id]
            else:
                ground = number(base)
                size = (
                    " × ".join(map(number, dim[:2])) + " m"
                    if dim
                    else (
                        "movable"
                        if kind == "rite"
                        else number(e.get("width_m", 0)) + " m span"
                    )
                )
                rule = PROPS[id]
            lines.append(
                f"| [{e['title']}](https://occult-kranti.github.io/ANDOLAN/production/mandala-art/#element={id}) | {ground} | {art} | {size} | {rule} |"
            )
        lines.append("")
    lines += [
        "## Production transfer",
        "",
        "Use the registered cover ID to share a collision shape among rendering, movement and projectile queries. Resurvey an opening after changing a sill, cover height or body size. A changed prop drawing alone does not certify a new hiding place. [Floor and route data](../maps/mandala.json) · [Surveyed shelter pairs](architecture.json) · [Trajectory fixtures](physics.json)",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "element-register.md"
    result = render()
    if args.check:
        if not path.exists() or path.read_text() != result:
            raise SystemExit("Regenerate element-register.md")
    else:
        path.write_text(result)
    print(
        "53 registered art subjects matched to their actual model extents and interaction rules."
    )
