/** Offline top-down rehearsal. Distances are metres in the atlas X/Z plane. */
const BODY_RADIUS = 0.45;
const FOOTSTEP_METRES = 1.65;
const SITE_IDS = ["a", "b"];
const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);

function project(point, a, b) {
  const dx = b[0] - a[0], dz = b[1] - a[1];
  const t = Math.max(0, Math.min(1,
    ((point[0] - a[0]) * dx + (point[1] - a[1]) * dz) / (dx * dx + dz * dz)));
  return Math.hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dz);
}

function inRoom(point, room, inset = 0) {
  return point.every((value, i) => Math.abs(value - room.xz[i]) <= room.size[i] / 2 - inset);
}

function coverDistance(point, cover) {
  return Math.hypot(...point.map((v, i) =>
    Math.max(0, Math.abs(v - cover.xz[i]) - cover.size[i] / 2)));
}

// Architectural sections arrive counterclockwise in the atlas X/Z plane.
function insideMasonry(point, ring) {
  return ring.every((b, i) => {
    const a = ring[(i + ring.length - 1) % ring.length];
    return (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0]) >= -1e-8;
  });
}

function boundMasonry({label, ring}) {
  const x = ring.map(p => p[0]), z = ring.map(p => p[1]);
  return {label, ring, bounds: [Math.min(...x), Math.min(...z), Math.max(...x), Math.max(...z)]};
}

function touchesMasonry(point, {ring, bounds: [l, s, r, n]}, radius) {
  if (point[0] < l - radius || point[0] > r + radius ||
      point[1] < s - radius || point[1] > n + radius) return false;
  if (insideMasonry(point, ring)) return true;
  return radius > 0 && ring.some((b, i) =>
    project(point, ring[(i + ring.length - 1) % ring.length], b) < radius);
}

/** Positive quarter turns are clockwise when north is up. */
function rotate(xz, turns) {
  switch ((turns % 4 + 4) % 4) {
    case 1: return [xz[1], -xz[0]];
    case 2: return [-xz[0], -xz[1]];
    case 3: return [-xz[1], xz[0]];
    default: return [...xz];
  }
}

function gateSign(gate, destination) {
  // On the architect's sign the stable waymark precedes its forward direction.
  const comma = gate.edge.cue.indexOf(",");
  const mark = comma > 0 ? gate.edge.cue.slice(0, comma).trim() + " · " : "";
  const turn = Math.abs(gate.turns) === 2 ? "Half turn" : gate.turns > 0 ? "Right turn" : "Left turn";
  return mark + turn + " to " + destination;
}

export class GroundPlan {
  constructor(data) {
    this.data = data;
    this.rooms = Object.entries(data.nodes);
    this.masonry = data.building.solids.map(boundMasonry);
    this.basins = data.building.water.map(boundMasonry);
    this.links = data.links.map(edge => {
      const points = [data.nodes[edge.from].xz, ...(edge.via ?? []), data.nodes[edge.to].xz];
      return {...edge, points};
    });
    this.segments = [];
    for (const edge of this.links) {
      if (edge.kind === "fold") continue;
      for (let i = 1; i < edge.points.length; i++) {
        const a = edge.points[i - 1], b = edge.points[i], half = edge.width / 2;
        this.segments.push({a, b, half, edge, bounds: [
          Math.min(a[0], b[0]) - half, Math.min(a[1], b[1]) - half,
          Math.max(a[0], b[0]) + half, Math.max(a[1], b[1]) + half]});
      }
    }
    this.wetRooms = new Set(this.rooms.filter(([id]) => {
      const exits = this.links.filter(e => e.from === id || e.to === id);
      return exits.length > 0 && exits.every(e => e.kind === "water");
    }).map(([id]) => id));
    this.folds = this.links.filter(e => e.kind === "fold");
  }

  segmentsAt(point) {
    return this.segments.filter(({bounds: [l, s, r, n]}) =>
      point[0] >= l && point[0] <= r && point[1] >= s && point[1] <= n);
  }

  canStand(point) {
    if (!point.every(Number.isFinite) ||
        this.data.cover.some(c => coverDistance(point, c) < BODY_RADIUS) ||
        this.masonry.some(piece => touchesMasonry(point, piece, BODY_RADIUS))) return false;
    // Erode each authored footprint. At joins this is conservative near the outer corner.
    return this.rooms.some(([, room]) => inRoom(point, room, BODY_RADIUS)) ||
      this.segmentsAt(point).some(s => project(point, s.a, s.b) <= s.half - BODY_RADIUS);
  }

  surface(point) {
    if (this.basins.some(basin => touchesMasonry(point, basin, 0))) {
      return {label: this.data.architecture.name, kind: "water"};
    }
    const room = this.rooms.find(([, n]) => inRoom(point, n));
    if (room) return {label: room[1].label, kind: this.wetRooms.has(room[0]) ? "water" : "room"};
    let nearest, best = Infinity;
    for (const segment of this.segmentsAt(point)) {
      const separation = project(point, segment.a, segment.b);
      if (separation <= segment.half && separation < best) {
        nearest = segment.edge;
        best = separation;
      }
    }
    if (!nearest) return {label: "Edge", kind: "walk"};
    const names = this.data.nodes;
    return {label: names[nearest.from].label + " – " + names[nearest.to].label, kind: nearest.kind};
  }

  atFold(point) {
    for (const edge of this.folds) {
      for (const key of ["from", "to"]) {
        const origin = this.data.nodes[edge[key]].xz;
        if (distance(point, origin) <= edge.width / 2 - BODY_RADIUS) {
          const destination = edge[key === "from" ? "to" : "from"];
          return {edge, key: edge[key], origin, destination,
            turns: key === "from" ? edge.quarter_turns : -edge.quarter_turns};
        }
      }
    }
    return null;
  }

  siteAt(point, radius) {
    return SITE_IDS.find(id => distance(point, this.data.nodes[id].xz) <= radius);
  }

  /** Sample the short interaction segment. The body and a placed vessel both stay on legal floor. */
  canReach(a, b, limit) {
    const length = distance(a, b);
    if (length > limit) return false;
    const steps = Math.max(1, Math.ceil(length / (BODY_RADIUS / 2)));
    for (let i = 1; i <= steps; i++) {
      if (!this.canStand(a.map((v, k) => v + (b[k] - v) * i / steps))) return false;
    }
    return true;
  }

  move(point, delta) {
    const candidate = point.map((v, i) => v + delta[i]);
    if (this.canStand(candidate)) return candidate;
    const x = [candidate[0], point[1]], z = [point[0], candidate[1]];
    if (Math.abs(delta[1]) > Math.abs(delta[0]) && this.canStand(z)) return z;
    if (this.canStand(x)) return x;
    return this.canStand(z) ? z : point;
  }
}

export class Rehearsal {
  constructor(plan, rules, mode = "explore", start = "atk", target = "a", onCue = null) {
    this.plan = plan;
    this.rules = rules;
    this.mode = mode;
    this.start = start;
    this.target = target;
    this.onCue = onCue;
    this.footstepMetres = 0;
    this.position = [...plan.data.nodes[start].xz];
    this.facing = start === "def" ? [0, -1] : [0, 1];
    this.phase = mode === "carry" ? "approach" : mode === "retake" ? "burn" : "explore";
    this.vessel = mode === "retake" ? [plan.data.nodes[target].xz[0], plan.data.nodes[target].xz[1] + 2] : null;
    this.carrying = mode === "carry";
    this.remaining = this.phase === "burn" ? rules.burn : rules.approach;
    this.elapsed = 0;
    this.progress = 0;
    this.channel = null;
    this.latched = false;
    this.started = false;
    this.message = mode === "retake" ? "The Ember is lit. Reach the marked vessel and quench it." :
      mode === "carry" ? "Carry the Ember into either site and hold to kindle." : "Walk the district or trace a route.";
  }

  stopChannel(canceled = false) {
    if (canceled && this.channel) this.onCue?.({type: "cancel"});
    this.channel = null;
    this.progress = 0;
  }

  interrupt() {
    if (!this.channel) return;
    this.stopChannel(true);
    this.latched = true;
    this.message = "Interrupted. Release Interact to begin another hold.";
  }

  drop() {
    if (this.phase !== "approach" || !this.carrying) return;
    this.carrying = false;
    this.vessel = [...this.position];
    this.stopChannel(true);
    this.latched = true;
    this.message = "Vessel dropped. Hold Interact within reach to recover it.";
    this.onCue?.({type: "drop"});
  }

  /** One deterministic local tick. Resolve completion before clock expiry, matching ritual.rs. */
  step({x = 0, z = 0, hold = false} = {}) {
    if (this.phase === "ended" || this.phase === "handoff") return;
    if (!hold) this.latched = false;
    if (x || z || hold) this.started = true;
    if (!this.started) return;
    this.elapsed++;
    const magnitude = Math.hypot(x, z);
    if (magnitude > 0) {
      this.facing = [x / magnitude, z / magnitude];
      const wet = this.plan.surface(this.position).kind === "water";
      const stride = this.rules.speed / this.rules.hz * (wet ? this.rules.water : 1);
      const before = this.position;
      this.position = this.plan.move(before, this.facing.map(v => v * stride));
      this.footstepMetres += distance(before, this.position);
      if (this.footstepMetres >= FOOTSTEP_METRES) {
        this.footstepMetres -= FOOTSTEP_METRES;
        const surface = this.plan.surface(this.position).kind === "water" ? "water" : "stone";
        this.onCue?.({type: "footstep", at: [...this.position], surface});
      }
    }

    const action = this.availableAction();
    if (!hold || this.latched || !action || (action.kind === "fold" && magnitude > 0)) {
      if (this.channel) this.message = hold ? "Hold interrupted." : "Hold released.";
      this.stopChannel(true);
    } else if (action.kind === "recover") {
      this.carrying = true;
      this.vessel = null;
      this.latched = true;
      this.stopChannel();
      this.message = "Ember recovered.";
      this.onCue?.({type: "recover"});
    } else {
      if (this.channel?.key !== action.key) {
        this.stopChannel(true);
        this.channel = action;
        const at = action.kind === "quench" ? this.vessel : this.position;
        this.onCue?.({type: action.kind + "_start", at: [...at], localHold: true});
      }
      this.progress++;
      if (this.progress >= action.duration) this.complete(action);
    }
    if (this.phase === "approach" || this.phase === "burn") {
      this.remaining--;
      if (this.remaining <= 0) {
        const type = this.phase === "burn" ? "burned" : "expired";
        this.message = this.phase === "burn" ? "The fire completed its burn." : "The approach clock expired.";
        this.phase = "ended";
        this.stopChannel();
        this.onCue?.({type});
      }
    }
  }

  availableAction() {
    if (this.phase === "ended" || this.phase === "handoff") return null;
    if (this.phase === "approach") {
      if (!this.carrying && this.vessel && this.plan.canReach(this.position, this.vessel, this.rules.reach)) {
        return {kind: "recover", key: "recover", duration: 1, name: "Recover vessel"};
      }
      const site = this.plan.siteAt(this.position, this.rules.siteRadius);
      if (this.carrying && site)
        return {kind: "kindle", key: "kindle-" + site, site, duration: this.rules.kindle, name: "Kindle " + site.toUpperCase()};
    }
    if (this.phase === "burn" && this.plan.canReach(this.position, this.vessel, this.rules.reach)) {
      return {kind: "quench", key: "quench", duration: this.rules.quench, name: "Quench the Ember"};
    }
    const gate = this.plan.atFold(this.position);
    if (!gate) return null;
    const destination = this.plan.data.nodes[gate.destination].label;
    return {kind: "fold", key: "fold-" + gate.key, gate, duration: Math.round(gate.edge.seconds * this.rules.hz),
      name: gateSign(gate, destination)};
  }

  complete(action) {
    this.latched = true;
    if (action.kind === "fold") {
      const gate = action.gate;
      const offset = this.position.map((v, i) => v - gate.origin[i]);
      const rotated = rotate(offset, gate.turns);
      const exit = this.plan.data.nodes[gate.destination];
      const landing = exit.xz.map((v, i) => v + rotated[i]);
      if (!this.plan.canStand(landing)) {
        this.stopChannel(true);
        this.message = "Exit obstructed. You remain at the entrance.";
        return;
      }
      this.position = landing;
      this.facing = rotate(this.facing, gate.turns);
      this.footstepMetres = 0;
      this.message = gateSign(gate, exit.label) + ". Crossing complete.";
      this.onCue?.({type: "fold", at: [...landing]});
    } else if (action.kind === "kindle") {
      this.vessel = [...this.position];
      this.carrying = false;
      this.target = action.site;
      this.phase = "handoff";
      this.remaining = this.rules.burn;
      this.message = "Site " + action.site.toUpperCase() + " kindled. Take the defender role to rehearse this exact placement.";
      this.onCue?.({type: "kindled", site: action.site});
    } else if (action.kind === "quench") {
      this.phase = "ended";
      this.message = "Quenched. The defenders contained the Ember.";
      this.onCue?.({type: "quenched"});
    }
    this.stopChannel();
  }

  takeDefence() {
    if (this.phase !== "handoff") return;
    this.phase = "burn";
    this.mode = "retake";
    this.start = this.target === "a" ? "b" : "a";
    this.position = [...this.plan.data.nodes[this.start].xz];
    this.facing = [0, 1];
    this.footstepMetres = 0;
    this.remaining = this.rules.burn;
    this.started = false;
    this.elapsed = 0;
    this.latched = true;
    this.message = "Retake from the opposite site. The clock starts on your first movement or interaction.";
    this.onCue?.({type: "handoff"});
  }

  turn(quarterTurns) {
    if (this.phase === "explore") this.facing = rotate(this.facing, quarterTurns);
  }
}
