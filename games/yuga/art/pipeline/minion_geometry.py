"""Original lightweight costumes and equipment for Yuga's seven NPC units.

Uses the repository's unchanged surface construction helpers. No downloaded
game geometry, texture, animation or executable modeling code is used here.
The naga and avian sentinel are deliberately grounded humanoid guardians.
"""
import math
from mathutils import Vector

TAU = math.tau


def frame(s, h, side='R'):
    bone = s.rig.data.bones['wrist.' + side]
    origin, rotation, scale = bone.head_local, bone.matrix_local.to_3x3(), h / 1.85
    palm = Vector((0, .105, .025 if side == 'R' else -.025))
    return lambda x, y, z: origin + rotation @ (Vector((z, y, -x)) + palm) * scale


def attire(s, c, m):
    h, width, kind = c['height'], c['width'], c['id']
    q = h / 1.85
    # Garments keep anatomical weights, including torso/hip deformation.
    s.fitted('Opaque fitted uniform', m['cloth'],
             lambda p: h * .54 < p.z < h * .82 and abs(p.x) < h * .145,
             .012 * q, neckline=h * .82)
    s.fitted('Woven trousers', m['cloth'], lambda p: h * .10 < p.z < h * .53, .020 * q)
    # A continuous rounded yoke covers the cut edge of the fitted torso after
    # reduction, instead of leaving a sawtooth neckline at the shoulders.
    def yoke(u, v):
        a = TAU * u
        return ((.073 + .153 * v) * q * width * math.cos(a),
                ((.085 + .075 * v) * math.sin(a) - .025) * q,
                h * .838 - .060 * q * v + .009 * q * math.cos(a * 2))
    s.cloth('Continuous rounded shoulder yoke', yoke, m['cloth'], rows=4, columns=24, wrap=True)
    s.tube('Collar rolled edge', [yoke(j / 24, 0) for j in range(25)], .006 * q, m['trim'], sides=5)
    armored = kind in ('soldier', 'king', 'yaksha')
    if armored:
        s.fitted('Curved breastplate', m['trim'],
                 lambda p: h * .63 < p.z < h * .79 and abs(p.x) < h * .12 and p.y < -.02,
                 .026 * q)
    skirt_length = .22 if kind in ('minister', 'naga') else .14
    def hem(u, v):
        a = TAU * u
        fold = (.004 + .009 * v) * math.cos(a * 12)
        return ((.15 + .075 * v + fold) * width * q * math.cos(a),
                (.14 + .04 * v + fold) * q * math.sin(a) + .015 * q,
                h * (.565 - skirt_length * v) + .015 * q * math.cos(a * 2))
    s.cloth('Pleated short tunic skirt', hem, m['cloth'], rows=5, columns=24, wrap=True)
    s.tube('Uniform hem braid', [hem(j / 24, 1) for j in range(25)], .004 * q, m['trim'], sides=5)
    s.ring('Waist belt', (0, .012 * q, h * .56), (.155 * width * q, .162 * q),
           m['dark'], 'spine05', .012 * q, segments=24)
    s.ellipsoid('Belt seal', (0, -.16 * q, h * .56), (.025 * q, .012 * q, .028 * q),
                m['trim'], 'spine05', segments=10, rings=6)
    for side in ('L', 'R'):
        arm = s.rig.data.bones['upperarm01.' + side].head_local
        if kind != 'sky-sentinel':
            s.ellipsoid('Curved shoulder guard ' + side, arm + Vector((0, 0, .012 * q)),
                        (.075 * q, .070 * q, .037 * q), m['trim'] if armored else m['cloth'],
                        'upperarm01.' + side, segments=12, rings=6)
        foot = s.rig.data.bones['foot.' + side].head_local
        s.ellipsoid('Closed soft boot ' + side, (foot.x, foot.y - .080 * q, .044 * q),
                    (.070 * q, .153 * q, .048 * q), m['dark'], 'foot.' + side, segments=14, rings=6)
        s.ring('Boot cuff ' + side, (foot.x, foot.y + .005 * q, h * .105),
               (.055 * q, .049 * q), m['trim'], 'lowerleg02.' + side, .007 * q, segments=16)
    # Small actual modeled strap rather than a new material/draw call.
    def sash(u, v):
        return ((.13 - .26 * v + (u - .5) * .075) * q * width,
                (-.18 - .012 * math.sin(v * math.pi)) * q,
                h * (.80 - .24 * v))
    if kind in ('city-watch', 'minister', 'king'):
        s.cloth('Diagonal office sash', sash, m['trim'], rows=9, columns=3)
    if kind in ('minister', 'king'):
        def mantle(u, v):
            return ((u - .5) * (.38 + .08 * v) * width * q,
                    (.10 + .11 * v + .012 * math.cos(u * TAU * 6)) * q,
                    h * (.81 - .40 * v))
        s.cloth('Short folded mantle', mantle, m['cloth'], rows=8, columns=12, bone='spine02')
        s.tube('Mantle lower braid', [mantle(j / 12, 1) for j in range(13)], .006 * q,
               m['trim'], 'spine02', sides=5)


def face(s, c, m):
    h, q, kind = c['height'], c['height'] / 1.85, c['id']
    for side in ('L', 'R'):
        eye = s.rig.data.bones['eye.' + side].head_local
        s.ellipsoid('Visible eye ' + side, eye + Vector((0, -.017 * q, 0)),
                    (.017 * q, .008 * q, .0065 * q), m['skin'], 'head', segments=10, rings=6)
        s.ellipsoid('Dark pupil ' + side, eye + Vector((0, -.0245 * q, 0)),
                    (.005 * q, .0015 * q, .005 * q), m['dark'], 'head', segments=8, rings=4)
        sign = 1 if side == 'L' else -1
        s.tube('Eyebrow ' + side,
               [(eye.x + sign * (j / 6 - .5) * .038 * q, eye.y - .024 * q,
                 eye.z + (.018 + .003 * math.sin(j / 6 * math.pi)) * q) for j in range(7)],
               .003 * q, m['dark'], 'head', sides=4)
    def cap(u, v):
        a, p = TAU * u, .03 + v * (1.52 + .15 * math.sin(TAU * u))
        return (.102 * c.get('face_width', 1) * q * math.sin(p) * math.cos(a),
                -.034 * q + .140 * q * math.sin(p) * math.sin(a),
                h * .948 + .12 * q * math.cos(p))
    s.cloth('Sculpted hair cap', cap, m['dark'], rows=6, columns=20, wrap=True, bone='head')
    if kind == 'city-watch':
        for k in range(4):
            pts = [(q * .113 * math.cos(TAU * j / 24), -.025 * q + q * .149 * math.sin(TAU * j / 24),
                    h * .965 + q * (.015 * k + .014 * math.cos(TAU * j / 24))) for j in range(25)]
            s.tube('Wrapped watch turban', pts, .018 * q, m['cloth'], 'head', sides=5)
        s.ellipsoid('Turban civic badge', (0, -.178 * q, h * .978),
                    (.022 * q, .009 * q, .028 * q), m['trim'], 'head', segments=8, rings=5)
    elif kind in ('soldier', 'minister'):
        s.ring('Low uniform circlet', (0, -.033 * q, h * .963),
               (.106 * q, .145 * q), m['trim'], 'head', .009 * q, segments=24)
        if kind == 'soldier':
            for sign in (-1, 1):
                s.ellipsoid('Helmet cheek plate', (sign * .077 * q, -.065 * q, h * .912),
                            (.014 * q, .05 * q, .043 * q), m['trim'], 'head', segments=10, rings=6)
        else:
            s.ellipsoid('Envoy topknot', (0, .035 * q, h * 1.012),
                        (.037 * q, .033 * q, .032 * q), m['dark'], 'head', segments=10, rings=6)
    elif kind == 'king':
        s.ring('Crown band', (0, -.033 * q, h * .96), (.11 * q, .145 * q),
               m['trim'], 'head', .012 * q, segments=24)
        for k in range(7):
            a = TAU * k / 7
            x, y = .108 * q * math.cos(a), -.033 * q + .145 * q * math.sin(a)
            s.mesh('Seven-point court crown', [(x - .018 * q, y, h * .96), (x + .018 * q, y, h * .96),
                    (x, y, h * .96 + .095 * q)], [(0, 1, 2), (2, 1, 0)], m['trim'], 'head')


def equipment(s, c, m):
    h, kind, q = c['height'], c['id'], c['height'] / 1.85
    p = frame(s, h)
    bone = 'wrist.R'
    if kind == 'sky-sentinel':
        return
    length = 1.24 if kind in ('soldier', 'minister', 'naga') else .83
    if kind == 'city-watch':
        # An original fictional compact carbine, only visual geometry. No
        # functional weapon internals, real manufacturer or copied model.
        s.tube('Watch carbine barrel', [p(0, 0, -.20), p(0, 0, .47)], .025 * q,
               m['dark'], bone, sides=8)
        s.tube('Watch barrel sleeve', [p(0, 0, .22), p(0, 0, .48)], .037 * q,
               m['trim'], bone, sides=8)
        verts = [p(x, y, z) for x, y, z in [(-.045, -.04, -.27), (.045, -.04, -.27),
                 (-.045, .07, -.27), (.045, .07, -.27), (-.038, -.04, .13), (.038, -.04, .13),
                 (-.038, .06, .13), (.038, .06, .13)]]
        s.mesh('Carved carbine stock', verts, [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
               (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)], m['cloth'], bone)
        s.tube('Stock foregrip', [p(0, .035, -.03), p(0, .13, -.03)], .028 * q, m['dark'], bone, sides=7)
        return
    s.tube('Carved hand-held shaft', [p(0, 0, -length * .32), p(0, 0, length * .68)],
           .018 * q if kind != 'yaksha' else .028 * q, m['dark'], bone, sides=8)
    for z in (-.08, .08, length * .55):
        s.tube('Shaft grip binding', [p(.021 * math.cos(TAU * j / 12), .021 * math.sin(TAU * j / 12), z)
               for j in range(13)], .004 * q, m['trim'], bone, sides=4)
    tip = length * .68
    if kind == 'soldier':
        # A double-sided, four-sided leaf point with thickness.
        verts = [p(0, 0, tip + .24), p(-.055, 0, tip + .075), p(0, -.014, tip),
                 p(.055, 0, tip + .075), p(0, .014, tip)]
        s.mesh('Leaf spear point', verts, [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1), (1, 4, 3, 2)], m['trim'], bone)
        left = frame(s, h, 'L')
        # Shield face lies beyond the knuckles; its grip crosses the closed palm.
        s.tube('Shield hand grip', [left(0, 0, -.08), left(0, 0, .08)], .018 * q, m['dark'], 'wrist.L')
        vertices = [left(.085, 0, 0)]
        vertices += [left(.02, .25 * math.sin(TAU * j / 20), .25 * math.cos(TAU * j / 20)) for j in range(20)]
        s.mesh('Convex round shield', vertices, [(0, 1 + j, 1 + (j + 1) % 20) for j in range(20)], m['cloth'], 'wrist.L')
        s.tube('Shield rolled rim', [left(.02, .25 * math.sin(TAU * j / 20), .25 * math.cos(TAU * j / 20)) for j in range(21)],
               .014 * q, m['trim'], 'wrist.L', sides=5)
        s.ellipsoid('Shield central boss', left(.095, 0, 0), (.040 * q, .040 * q, .040 * q), m['trim'], 'wrist.L', segments=10, rings=6)
    elif kind in ('king', 'yaksha'):
        s.ellipsoid('Fluted mace' if kind == 'king' else 'Grove knotted club', p(0, 0, tip),
                    (.105 * q, .10 * q, .13 * q), m['trim'] if kind == 'king' else m['cloth'], bone, segments=14, rings=8, ridge=.16)
        if kind == 'king':
            # Small back-mounted standard is ceremonial, not another hitbox.
            s.tube('Court standard pole', [(0, .17 * q, h * .57), (0, .17 * q, h * 1.17)],
                   .013 * q, m['dark'], 'spine02', sides=6)
            def flag(u, v):
                return ((u * .30 + .02) * q, (.18 + .025 * math.sin(u * math.pi * 2 + v)) * q,
                        h * 1.15 - v * .25 * q)
            s.cloth('Crown envoy court banner', flag, m['cloth'], rows=4, columns=7, bone='spine02')
            s.tube('Standard gold edge', [flag(j / 7, 1) for j in range(8)], .006 * q, m['trim'], 'spine02', sides=4)
    else:
        s.tube('Ceremonial staff loop', [p(.085 * math.sin(TAU * j / 20), 0, tip + .095 + .095 * math.cos(TAU * j / 20)) for j in range(21)],
               .012 * q, m['trim'], bone, sides=6)
        s.ellipsoid('Staff polished seal', p(0, 0, tip + .09), (.032 * q, .026 * q, .045 * q), m['cloth'], bone, segments=10, rings=6)
        if kind == 'minister':
            left = frame(s, h, 'L')
            s.tube('Rolled envoy document', [left(0, 0, -.12), left(0, 0, .12)], .024 * q, m['trim'], 'wrist.L', sides=10)
            s.tube('Document dark seal band', [left(0, 0, -.018), left(0, 0, .018)], .026 * q, m['dark'], 'wrist.L', sides=10)


def guardian(s, c, m):
    h, q, kind = c['height'], c['height'] / 1.85, c['id']
    if kind == 'yaksha':
        for i in range(7):
            x = (i - 3) * .015 * q
            length = (.065 - abs(i - 3) * .009) * q
            s.mesh('Carved leafy chin beard', [(x - .010 * q, -.13 * q, h * .88),
                   (x + .010 * q, -.13 * q, h * .88), (x, -.14 * q, h * .88 - length),
                   (x, -.15 * q, h * .875)], [(0, 1, 3), (1, 2, 3), (2, 0, 3)], m['dark'], 'head')
        for sign in (-1, 1):
            pts = [(sign * (.078 + .075 * t), (.02 + .04 * t) * q, h * .99 + .14 * q * t)
                   for t in (0, .25, .5, .75, 1)]
            s.tube('Forked grove horn', pts, .025 * q, m['dark'], 'head', sides=7, taper=lambda t: 1 - .92 * t)
            for i in range(3):
                x = sign * (.12 + .034 * i) * q
                s.ellipsoid('Layered bark shoulder', (x, .025 * q, h * .79 - .025 * q * i),
                            (.052 * q, .07 * q, .065 * q), m['cloth'], 'upperarm01.' + ('L' if sign > 0 else 'R'), segments=8, rings=5, ridge=.12)
        for i in range(4):
            s.tube('Carved guardian chest channel', [(-.10 * q, -.19 * q, h * (.69 + .026 * i)),
                   (0, -.215 * q, h * (.67 + .026 * i)), (.10 * q, -.19 * q, h * (.69 + .026 * i))],
                   .006 * q, m['dark'], sides=5)
    elif kind == 'naga':
        # A double-sided cobra-like collar is ornamental. Native neck weighting
        # follows grounded biped motion; this is not a serpent movement rig.
        def hood(u, v):
            a = math.pi * u
            return (math.cos(a) * (.13 + .15 * math.sin(v * math.pi)) * q,
                    (.035 + .08 * math.sin(a)) * q,
                    h * .79 + v * .32 * q)
        front = s.cloth('Reed naga flared hood', hood, m['cloth'], rows=8, columns=16, bone='neck01')
        # Explicit reversed faces, no material double-sided ambiguity.
        verts = [v.co.copy() for v in front.data.vertices]
        s.mesh('Hood reverse surface', verts, [list(reversed(p.vertices)) for p in front.data.polygons], m['cloth'], 'neck01')
        for u in (0, .25, .5, .75, 1):
            s.tube('Hood carved ribs', [Vector(hood(u, j / 8)) + Vector((0, -.005, 0)) for j in range(9)],
                   .004 * q, m['trim'], 'neck01', sides=4)
        pts = [(.20 * q * math.sin(t * math.pi * 1.5), (.13 + .48 * t) * q,
                h * .51 - .55 * q * t + .18 * q * math.sin(t * math.pi)) for t in [j / 16 for j in range(17)]]
        s.tube('Grounded naga ornamental tail', pts, .048 * q, m['cloth'], 'spine05', sides=8, taper=lambda t: 1 - .94 * t)
    elif kind == 'sky-sentinel':
        # Native elbow/wrist deformation makes folded wings flare during fire.
        # Feathers are authored around the source arm, with no flight state.
        for side, sign in (('L', 1), ('R', -1)):
            upper = s.rig.data.bones['upperarm01.' + side]
            lower = s.rig.data.bones['lowerarm01.' + side]
            for i in range(8):
                t = i / 7
                root = upper.head_local.lerp(lower.tail_local, t)
                length = (.16 + .15 * math.sin(t * math.pi)) * q
                tip = root + Vector((sign * .05 * q, .065 * q, -length))
                width = .032 * q
                mid = root.lerp(tip, .45)
                bone = 'upperarm01.' + side if t < .45 else 'lowerarm01.' + side
                s.mesh('Layered folded flightless feather', [root, mid + Vector((width, -.015 * q, 0)), tip,
                       mid + Vector((-width, .015 * q, 0)), mid + Vector((0, -.024 * q, 0))],
                       [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (3, 2, 1, 0)],
                       m['cloth'] if i % 2 else m['trim'], bone)
        # Smooth beaked mask follows the existing actual anatomical face.
        s.mesh('Avian tapered beak', [(-.033 * q, -.155 * q, h * .918), (.033 * q, -.155 * q, h * .918),
               (0, -.255 * q, h * .89), (0, -.17 * q, h * .88), (0, -.175 * q, h * .93)],
               [(0, 2, 4), (2, 1, 4), (0, 3, 2), (3, 1, 2), (0, 4, 1, 3)], m['trim'], 'head')
        for i in range(5):
            x = (i - 2) * .027 * q
            s.mesh('Sentinel head plume', [(x - .012 * q, 0, h * .98), (x + .012 * q, 0, h * .98),
                   (x, .07 * q, h + (.12 - .02 * abs(i - 2)) * q)], [(0, 1, 2), (2, 1, 0)], m['cloth'], 'head')


def sculpt_unit(s, c, materials):
    attire(s, c, materials)
    face(s, c, materials)
    guardian(s, c, materials)
    equipment(s, c, materials)
