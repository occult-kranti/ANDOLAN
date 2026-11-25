#!/usr/bin/env python3
"""Generate and verify the 14-hero classic Rust sparring design catalog."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ROSTER = ROOT / 'games/yuga-rust/assets/classic-roster.json'
ABILITY_CODE = ROOT / 'games/yuga-rust/src/bin/roster/abilities.rs'
LAB_CODE = ROOT / 'games/yuga-rust/src/bin/roster/lab.rs'

# Each pair is a proposed animation/FX layer and a counterplay or QA question.
# Ordering is primary, Q, E and R from the actual roster.
DIRECTION = {
    'rama': [
        ('Draw the compact bow silhouette and keep the string hand visible.', 'Move during repeat fire and verify a wall ends the projectile.'),
        ('Lengthen the bow arm and draw a narrow, steady sightline.', 'Sidestep or hide behind cover and verify one bolt contact.'),
        ('Shift the feet under the bow without turning the held aim into a hitbox.', 'Step into a wall and verify the shortened endpoint.'),
        ('Show three separate sightlines during the draw and release together.', 'Block one path and check three simultaneous, independently colliding arrows.'),
    ],
    'ravana': [
        ('Keep the ring blade outside the crown silhouette before the ranged release.', 'Verify the visible disc is a projectile and stops at cover.'),
        ('Close the broad mantle into a protective silhouette and place brackets on eligible allies.', 'Place an ally outside the radius and another behind cover.'),
        ('Turn an open right palm toward a marked center, then draw a segmented inward pull.', 'Check the pull moves at most six metres and a wall limits it.'),
        ('Raise the crown and open a broken full-circle boundary around the caster.', 'Leave the radius or hide behind solid cover before resolution.'),
    ],
    'arjuna': [
        ('Track the aim line along the long bow while keeping the high quiver visible.', 'Move across the firing line and verify a single projectile hit.'),
        ('Expand the drawn bow into an open forward fan with a distinct edge.', 'Test one target just inside and outside the fan angle.'),
        ('Let the split scarf lag the footfall as the archer repositions.', 'Dash against cover and check the actual endpoint.'),
        ('Narrow the shoulders and use one straight elongated trail.', 'Step sideways and verify one fast shot stops at cover.'),
    ],
    'duryodhana': [
        ('Show the heavy mace at the side while the ranged primary leaves along aim.', 'Confirm the apparent mace scale does not suggest a melee-only hit.'),
        ('Sink the shoulders into a short front-facing impact fan.', 'Test a target beyond the range and one behind the caster.'),
        ('Plant the stance and give protected allies a firm square ward edge.', 'Move an ally beyond the circle or behind cover before the grant.'),
        ('Sweep the heavy mace into a broad wedge with visible side limits.', 'Check one receiver on either side of the cone threshold.'),
    ],
    'hanuman': [
        ('Keep the rounded mace and tail clear as the classic ranged shot leaves.', 'Confirm this sparring primary uses a projectile.'),
        ('Compress the rear leg, then extend the tail to counterbalance travel.', 'Compare a clear leap and a wall-shortened endpoint.'),
        ('Offer the open hand and connect an arc only to healed recipients.', 'Test a damaged ally, a full-health ally and an ally behind cover.'),
        ('Lift the mountain through the 0.7 s brace, then travel with a clear landing disk.', 'Move out of the landing radius or stop travel against cover.'),
    ],
    'karna': [
        ('Angle the crescent bow so the radiant shoulder discs frame the release.', 'Use cover and verify a single shot terminates at the wall.'),
        ('Pin a bright, narrow line between bow and accepted target.', 'Move across the line before the projectile reaches the target.'),
        ('Turn the shoulder discs outward and give allies a distinct ward outline.', 'Compare shielded allies inside and outside the 4 m circle.'),
        ('Collect the shoulder light inward before a single circular flash.', 'Leave the six-metre radius and verify blocking cover.'),
    ],
    'bhima': [
        ('Keep the long mace readable while a separate ranged primary travels forward.', 'Verify a distant opponent can be hit only by the projectile.'),
        ('Rotate the broad torso into a single close fan.', 'Check front, side and behind positions against the cone.'),
        ('Bend into the leap and hold the mace near the torso during travel.', 'Clip travel against a wall and locate the actual endpoint.'),
        ('Plant both feet and send one low ring outward.', 'Move past the eight-metre radius and confirm one damage event.'),
    ],
    'meghnad': [
        ('Keep the forked crest and compact bow clear of the cloud scarf.', 'Verify moving fire and the projectile boundary at cover.'),
        ('Mark a fixed cloud field with a broken outer edge and a fading center.', 'Enter, exit and re-enter; check ticking damage and the remaining slow.'),
        ('Tilt the scarf opposite the step while the movement path remains clear.', 'Stop at a wall and keep aim readable.'),
        ('Unfold the compact bow into a long fan with spaced edge marks.', 'Test a target across the fan edge and behind cover.'),
    ],
    'sita': [
        ('Lead with the leaf-tipped staff and keep its shot distinct from healing.', 'Confirm the ranged shot terminates on cover.'),
        ('Open the staff hand and use brief leaf-shaped marks on healed allies.', 'Test full-health allies, range boundaries and blocked sight.'),
        ('Trace a fixed rooted perimeter with gaps that keep moving enemies visible.', 'Leave the zone and check its slow expiry separately from the animation.'),
        ('Gather the mantle during the brace, then raise a stable sanctuary perimeter.', 'Interrupt before release and test the one-time ward plus ongoing field heal.'),
    ],
    'draupadi': [
        ('Keep the flame staff separate from the five-point mantle clasp.', 'Confirm the basic projectile has one contact at a wall or enemy.'),
        ('Gather the mantle at the chest before opening ally ward brackets.', 'Check allied recipients within radius and behind solid cover.'),
        ('Point the staff at a marked center and show a measured inward pull.', 'Use a wall to limit displacement and check pull distance.'),
        ('Lift both forearms and show one broad, open healing ring.', 'Leave the radius or block sight and verify no heal receipt.'),
    ],
    'subhadra': [
        ('Keep the spear pennant trailing behind the forward ranged projectile.', 'Verify the basic shot stops at the first contact.'),
        ('Extend the spear and release one narrow lance along the aim.', 'Hide behind cover and verify a single bolt impact.'),
        ('Lower the spear and show short arcs only on healed allies.', 'Test the four-metre boundary, including a full-health ally.'),
        ('Plant two standards, then resolve each sentinel at its actual spawn point.', 'Block one spawn and test actor limits, expiry and ownership.'),
    ],
    'hidimbi': [
        ('Hold the forked spear outside the broad leaf mantle while firing.', 'Verify the primary projectile is distinct from a melee sweep.'),
        ('Use leaf-shaped notches along a fixed field boundary.', 'Cross the five-metre edge and check slow persistence.'),
        ('Close the mantle into a protective arc and bracket real shield recipients.', 'Place one ally behind cover and one beyond the radius.'),
        ('Open two clear spaces under the canopy for the actual sentinel spawns.', 'Check blocked spawns, ally ownership and nine-second expiry.'),
    ],
    'chitrangada': [
        ('Frame the crescent spear outside the short mantle during a ranged shot.', 'Confirm the visible projectile and first hit match authority.'),
        ('Lead with the stepping foot and keep the spear free of the moving leg.', 'Dash into a wall and check movement ends at the collision.'),
        ('Turn the crescent tip into a distinct forward wedge.', 'Test edge angles, range and a target behind cover.'),
        ('Square the segmented mantle and place thin ward brackets on allies.', 'Check the six-metre boundary and stronger pre-existing shield.'),
    ],
    'ulupi': [
        ('Keep the water-ring staff visible as the ranged primary travels.', 'Use cover and verify a single projectile hit.'),
        ('Draw a marked water center with an inward-moving broken ring.', 'Confirm the six-metre pull limit and wall-limited movement.'),
        ('Turn the staff across the torso and display restrained ripples at healed allies.', 'Compare injured, full-health and occluded allies.'),
        ('Keep a broad basin perimeter visible through muted water particles.', 'Cross the radius and check damage ticks, slow and six-second expiry.'),
    ],
}
KEYS = ('Q', 'E', 'R')


def number(v):
    return str(v)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mechanic(a):
    k = a['kind']
    special = a.get('mechanic')
    cd = f"{number(a['cooldown'])} s cooldown"
    if special == 'dawn-volley':
        return f"{a['windup']} s windup; three simultaneous {a['power']}-damage arrows; {a['range']} m range; {cd}"
    if special == 'mountain-descent':
        return f"{a['windup']} s windup and 0.45 s travel; up to {a['range']} m; {a['radius']} m landing radius; {a['power']} enemy damage and 45 allied healing; {cd}"
    if special == 'mithila-sanctuary':
        return f"{a['windup']} s windup; {a['radius']} m radius; {a['power']} initial ward and 9 healing/s in the field for {a['duration']} s; {cd}"
    if k in ('bolt', 'line'):
        return f"{a['power']} damage; {a['range']} m range; {38 if k == 'bolt' else 62} m/s projectile; {cd}"
    if k in ('burst', 'cone'):
        return f"{a['power']} damage; {a['range']} m front fan; {cd}"
    if k == 'nova':
        return f"{a['power']} damage; {a['radius']} m caster-centered radius; {cd}"
    if k in ('heal', 'ward'):
        text = f"{a['power']} {'healing' if k == 'heal' else 'shield'}; {a['radius']} m ally radius"
        if k == 'ward':
            text += f"; {a['duration']} s ward"
        return text + '; ' + cd
    if k in ('dash', 'leap'):
        return f"up to {a['range']} m movement, blocked by solids; {cd}"
    if k == 'slow':
        rate = a['power'] / max(a['duration'], 1)
        return f"{a['range']} m placement range; {a['radius']} m radius for {a['duration']} s; nominal {rate:g} damage/s while inside; {cd}"
    if k == 'pull':
        return f"{a['power']} damage in a {a['radius']} m aimed circle; up to 6 m pull; {a['range']} m placement range; {cd}"
    if k == 'summon':
        return f"up to two allied sentinels with 105 HP and {a['power']} attack; {max(a['duration'] * 3, 6)} s lifetime; {cd}"
    raise ValueError(f'Unknown classic kind or mechanic {k}/{special}')


def build():
    source = json.loads(ROSTER.read_text())
    heroes = source['heroes']
    if len(heroes) != 14 or len({h['id'] for h in heroes}) != 14:
        raise ValueError('Expected 14 distinct roster heroes')
    if set(DIRECTION) != {h['id'] for h in heroes}:
        raise ValueError('Curated visual direction no longer matches the roster')
    if any(len(h['abilities']) != 3 or len(DIRECTION[h['id']]) != 4 for h in heroes):
        raise ValueError('Expected 14 primaries and 42 ability directions')
    out = [
        '# Classic Rust sparring · all 14 heroes',
        '',
        'The classic Rust sparring roster has one primary and Q/E/R for each of 14 heroes. This is a separate product from Rust Confluence, whose Hanuman and Rama have five-action kits. The rows below state the current classic mechanics and propose animation or effect layers for production review. They do not grant new effects. [Classic launch and verification](../../rust-rebuild/deep-search/CLASSIC-DISTRIBUTION.md) · [Confluence design](HANUMAN_RAMA.md)',
        '',
        'Every classic primary uses an authority projectile, including staff, mace and spear heroes. Speed, damage and authored repeat interval below come from the hero profile. Melee-looking weapon animation must still reveal a traveling shot. A projectile stops at its first enemy or solid contact. The simulation advances at 20 Hz. [Primary fire](../../../../yuga-rust/src/bin/roster/lab.rs) · [Roster profile](../../../../yuga-rust/assets/classic-roster.json)',
        '',
        'Immediate front fans, circle damage and support checks require line of sight. A slow field follows an accepted ground point and refreshes a 0.5 s slow status while an enemy remains inside. Its listed per-second rate is the authored power divided by its lifetime and must be validated at tick boundaries. Dashes and ordinary leaps move against world collision and do not use the profile’s generic power as contact damage. Summons can produce fewer than two units when placement or actor limits prevent a spawn. [Classic cast dispatcher](../../../../yuga-rust/src/bin/roster/abilities.rs) · [Zone ticks](../../../../yuga-rust/src/bin/roster/lab.rs)',
        '',
        'Color never carries team or danger information alone. Every directional fan, circle, accepted impact and ally receipt also needs a shape, icon or label that works with reduced motion and muted audio. The listed counterplay is a review intent to test, not a claim from a human study. [Accessibility guidance](https://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-a-fixed-colour-alone/)',
        '',
        f"The source snapshot SHA-256 values are roster `{digest(ROSTER)}`, cast dispatcher `{digest(ABILITY_CODE)}`, and match simulation `{digest(LAB_CODE)}`. Regenerate this file after any source change using `python3 games/yuga-native/docs/design/combat-panel-2026/classic_roster.py`, then run the same command with `--check`.",
        '',
    ]
    for h in heroes:
        out.extend([f"## {h['name']} · {h['role']}", '',
                    f"The current silhouette is {h['silhouette'].lower()}.", '',
                    '| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |',
                    '| --- | --- | --- | --- |'])
        cue, qa = DIRECTION[h['id']][0]
        primary = f"{h['damage']} damage; {h['projectileSpeed']} m/s; authored {h['fireInterval']} s repeat"
        out.append(f"| Primary · {h['weapon'].title()} | {primary} | {cue} | {qa} |")
        for index, ability in enumerate(h['abilities']):
            cue, qa = DIRECTION[h['id']][index + 1]
            out.append(f"| {KEYS[index]} · {ability['name']} | {mechanic(ability)} | {cue} | {qa} |")
        out.append('')
    return '\n'.join(out).rstrip() + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    file = HERE / 'CLASSIC_ROSTER.md'
    text = build()
    if args.check:
        if file.read_text() != text:
            raise ValueError('Classic catalog differs from source or reviewed visual direction')
        print('Verified 14 heroes, 14 primaries and 42 named actions against current source.')
    else:
        file.write_text(text)
        print(file)


if __name__ == '__main__':
    main()
