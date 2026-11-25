#!/usr/bin/env python3
"""Draw and validate a conceptual route graph, not runtime world geometry."""
from collections import Counter, defaultdict
from heapq import heappop, heappush
from math import hypot, isclose
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'map-spec.json').read_text())
nodes = {name: tuple(row['xz']) for name, row in data['nodes'].items()}
edges = data['edges']
speed = data['baseline_walk_mps']
water = data['water_speed_multiplier']

def elapsed(edge):
    if edge['kind'] == 'portal':
        return edge['travel_seconds']
    a, b = nodes[edge['a']], nodes[edge['b']]
    length = hypot(a[0] - b[0], a[1] - b[1])
    return length / (speed * (water if edge['kind'] == 'water' else 1))

def times(origin, include_portals):
    graph = defaultdict(list)
    for edge in edges:
        if not include_portals and edge['kind'] == 'portal':
            continue
        a, b = edge['a'], edge['b']
        graph[a].append((b, elapsed(edge)))
        graph[b].append((a, elapsed(edge)))
    distances = {origin: 0.}
    queue = [(0., origin)]
    while queue:
        d, node = heappop(queue)
        if d != distances[node]:
            continue
        for nxt, cost in graph[node]:
            candidate = d + cost
            if candidate < distances.get(nxt, float('inf')):
                distances[nxt] = candidate
                heappush(queue, (candidate, nxt))
    return distances

def edge_key(edge, mirror=False):
    def xy(name):
        x, z = nodes[name]
        return (x, -z if mirror else z)
    return (tuple(sorted((xy(edge['a']), xy(edge['b'])))), edge['kind'], edge.get('travel_seconds'))

assert len(nodes) == 23 and len(edges) == 30
assert all(e['a'] in nodes and e['b'] in nodes for e in edges)
assert Counter(edge_key(e) for e in edges) == Counter(edge_key(e, True) for e in edges)
results = {}
for portals in (False, True):
    sun, moon = times('sun_spawn', portals), times('moon_spawn', portals)
    assert len(sun) == len(moon) == len(nodes), 'Every route needs a non-portal alternative.'
    rows = {}
    for label, node in data['objectives'].items():
        assert isclose(sun[node], moon[node], abs_tol=1e-9), label
        rows[label] = {'sun_seconds': round(sun[node], 3), 'moon_seconds': round(moon[node], 3)}
    results['portals_enabled' if portals else 'walking_only'] = rows
receipt = {
    'status': 'pass', 'scope': 'abstract mirrored route graph only',
    'nodes': len(nodes), 'edges': len(edges), 'all_reachable_without_portals': True,
    'symmetric_edges': True, 'first_arrival_estimates': results,
    'limitations': 'No collision geometry, line-of-sight, gameplay, network, art or player-speed measurement is established.',
}
(HERE / 'plan-validation.json').write_text(json.dumps(receipt, indent=2) + '\n')

plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none'})
fig = plt.figure(figsize=(15.6, 9.6), facecolor='#101d1d')
grid = fig.add_gridspec(1, 2, width_ratios=[1.06, 1], wspace=.1, left=.035, right=.975, top=.91, bottom=.065)
ax = fig.add_subplot(grid[0, 0]); side = fig.add_subplot(grid[0, 1]); side.axis('off')
ax.set_facecolor('#29352e'); ax.set_xlim(-77, 77); ax.set_ylim(-130, 130); ax.set_aspect('equal'); ax.axis('off')
ax.add_patch(FancyBboxPatch((-68, -123), 136, 246, boxstyle='round,pad=0,rounding_size=9',
                            facecolor='#354239', edgecolor='#8e9b85', linewidth=1.2))
ax.add_patch(Ellipse((-42, 0), 34, 145, facecolor='#25645e', edgecolor='#72bcb0', alpha=.7, lw=1.4))
ax.add_patch(Ellipse((-43, -52), 21, 45, facecolor='#286b60', edgecolor='none', alpha=.75))
ax.add_patch(Ellipse((-43, 52), 21, 45, facecolor='#286b60', edgecolor='none', alpha=.75))
ax.add_patch(FancyBboxPatch((30, -25), 26, 50, boxstyle='round,pad=1,rounding_size=3',
                            facecolor='#785743', edgecolor='#cba16d', linewidth=1.3, alpha=.95))
ax.add_patch(Circle((0, 0), 13, facecolor='#a87a4e', edgecolor='#ffdaa0', linewidth=1.4, zorder=2))
for e in edges:
    a, b = nodes[e['a']], nodes[e['b']]
    if e['kind'] == 'portal':
        ax.plot([a[0], b[0]], [a[1], b[1]], color='#ffd180', linewidth=2.2,
                linestyle=(0, (2.5, 2.0)), zorder=5)
    else:
        ax.plot([a[0], b[0]], [a[1], b[1]], color='#17221f', linewidth=8.8, solid_capstyle='round', zorder=1)
        ax.plot([a[0], b[0]], [a[1], b[1]], color='#8fcac2' if e['kind'] == 'water' else '#d6c09b',
                linewidth=4.9, solid_capstyle='round', zorder=2)
for key in ('temple_portal_s', 'pyramid_portal_s', 'temple_portal_n', 'pyramid_portal_n'):
    x, z = nodes[key]
    ax.plot(x, z, marker='D', ms=7, color='#ffd180', markeredgecolor='#332414', zorder=6)
for key, color, title in [('sun_spawn', '#f4ba73', 'SUN'), ('moon_spawn', '#8dd6ef', 'MOON')]:
    x, z = nodes[key]; ax.scatter(x, z, s=380, c=color, edgecolors='#151c1a', linewidths=1.5, zorder=7)
    ax.text(x, z, title, ha='center', va='center', color='#10201f', fontsize=7.5, weight='bold', zorder=8)
for node, label in [('site_a', 'A'), ('site_b', 'B')]:
    x, z = nodes[node]; ax.scatter(x, z, s=480, c='#f1d398', edgecolors='#30291f', linewidths=1.3, zorder=7)
    ax.text(x, z, label, color='#2e291d', fontsize=12, weight='bold', ha='center', va='center', zorder=8)
ax.text(-42, 4, 'RIVER\nJUNGLE', color='#e7faf0', fontsize=8, weight='bold', ha='center', zorder=8)
ax.text(0, 18, 'MANDAPA', color='#f8e9ca', fontsize=7.5, weight='bold', ha='center', zorder=8)
ax.text(42, 15, 'BAZAAR', color='#f8e9ca', fontsize=7.5, weight='bold', ha='center', zorder=8)
ax.text(20, 38, 'FOLD N', color='#ffda9b', fontsize=6.5, ha='center', zorder=8)
ax.text(20, -40, 'FOLD S', color='#ffda9b', fontsize=6.5, ha='center', zorder=8)
fig.text(.045, .96, 'YUGA / MANDALA RIFT', color='#fff3dc', fontsize=22, weight='bold', va='top')
fig.text(.046, .922, '5v5 CONCEPT  ·  THREE APPROACHES  ·  TWO PROPOSED SITES', color='#9bc2b6', fontsize=10)
side.text(0, .98, 'A tactical arena with a hidden interior', color='#f8e8ca', fontsize=17, weight='bold', va='top', transform=side.transAxes)
lines = [
    ('01  /  GHAT JUNGLE', 'Shallow water, stone ford and mangrove cover.\nA dry route remains available on both sides.'),
    ('02  /  MANDAPA · A', 'An open temple court and two readable entrances.\nShelter the sites from immediate spawn sightlines.'),
    ('03  /  BAZAAR · B', 'A city-edge market meets a stepped shrine.\nShort cover pieces make flanks visible and contestable.'),
    ('04  /  FOLDED INTERIORS', 'Two mirrored temple ↔ pyramid links. Portals are\naudible and bidirectional; a walking route remains.'),
    ('05  /  FIVE AGAINST FIVE', 'Design target: objective rounds and hero abilities.\nNo soldier waves. Existing models remain reusable.'),
]
for i, (title, text) in enumerate(lines):
    y = .88 - i * .145
    side.text(0, y, title, color='#efbd7b', fontsize=10.5, weight='bold', va='top', transform=side.transAxes)
    side.text(0, y - .035, text, color='#d5dfd4', fontsize=10, va='top', linespacing=1.5, transform=side.transAxes)
side.plot([0, .12], [.13, .13], color='#d6c09b', linewidth=5, transform=side.transAxes)
side.text(.15, .13, 'walkable path', color='#d5dfd4', fontsize=9, va='center', transform=side.transAxes)
side.plot([.43, .55], [.13, .13], color='#8fcac2', linewidth=5, transform=side.transAxes)
side.text(.58, .13, 'shallow water', color='#d5dfd4', fontsize=9, va='center', transform=side.transAxes)
side.plot([0, .12], [.085, .085], color='#ffd180', linewidth=2.2, linestyle=(0, (2.5, 2)), transform=side.transAxes)
side.text(.15, .085, 'optional folded link', color='#d5dfd4', fontsize=9, va='center', transform=side.transAxes)
side.text(0, .01, 'DESIGN SKETCH · route positions and timings are proposals, not game collision.',
          color='#a6bdb0', fontsize=8.6, transform=side.transAxes)
fig.savefig(HERE / 'map-sketch.png', dpi=150, facecolor=fig.get_facecolor())
svg_path = HERE / 'map-sketch.svg'
fig.savefig(svg_path, facecolor=fig.get_facecolor())
svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text().splitlines()) + '\n')
print(json.dumps(receipt, indent=2))
