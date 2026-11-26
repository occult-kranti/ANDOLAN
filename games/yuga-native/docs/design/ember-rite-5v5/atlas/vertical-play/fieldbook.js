const field = JSON.parse(document.getElementById("field-data").textContent);
const ui = (id) => document.getElementById(id);
const ns = "http://www.w3.org/2000/svg";
const short = (value) => Number(value.toFixed(2)).toString();
const pointLabel = (p) => p.map(short).join(", ");
function svgNode(parent, tag, attributes, text) {
  const node = document.createElementNS(ns, tag);
  Object.entries(attributes).forEach(([key, value]) =>
    node.setAttribute(key, value),
  );
  if (text !== undefined) node.textContent = text;
  parent.append(node);
  return node;
}
function options(select, choices) {
  select.replaceChildren(
    ...choices.map(([id, label]) => new Option(label, id)),
  );
}
function own(id) {
  return field.maps.find((map) => map.id === id);
}
function chosenEntrance() {
  return activeMap.entrances.find((entry) => entry.id === ui("door").value);
}
let activeMap,
  ground,
  actor,
  walking = false,
  convert;
let activeMarks = [];
function pickDistrict() {
  activeMap = own(ui("district").value);
  ground = new GroundPlan(activeMap);
  options(
    ui("court"),
    ["a", "b"].map((k) => [
      k,
      "Site " + k.toUpperCase() + " · " + activeMap.nodes[k].label,
    ]),
  );
  pickCourt();
}
function pickCourt() {
  options(
    ui("door"),
    activeMap.entrances
      .filter((e) => e.site === ui("court").value)
      .map((e) => [e.id, activeMap.nodes[e.approach].label]),
  );
  ui("face").value = "approach";
  pickDoor();
}
function pickDoor() {
  const entry = chosenEntrance(),
    reverse = !!entry.pockets[0].reverse_threat_xz;
  ui("face-label").hidden = !reverse;
  if (!reverse) ui("face").value = "approach";
  walking = false;
  actor = null;
  ui("walk").textContent = "Walk this entrance";
  ui("walk-info").textContent = "Start at the observer and try both shelters.";
  drawCourt();
}
function drawCourt() {
  const svg = ui("plan"),
    entry = chosenEntrance(),
    room = activeMap.nodes[entry.site];
  const approach = activeMap.nodes[entry.approach].label,
    rev = ui("face").value === "reverse";
  const prefix = rev ? "reverse_" : "";
  const coverById = new Map(activeMap.studyCovers.map((c) => [c.id, c]));
  activeMarks = entry.pockets.map((p) => ({
    data: p,
    cover: coverById.get(p.cover_id),
    hide: p[prefix + "body_hide_xz"] || p[prefix + "hide_xz"],
    shoulder: p[prefix + "hide_xz"],
    peek: p[prefix + "peek_xz"],
    threat: p[prefix + "threat_xz"],
  }));
  const samples = [
    ...activeMarks.flatMap((p) => [p.hide, p.peek, p.threat]),
    entry.mouth_xz,
  ];
  const [cx, cz] = room.xz,
    [w, d] = room.size,
    xs = samples.map((p) => p[0]),
    zs = samples.map((p) => p[1]);
  const left = Math.min(cx - w / 2, ...xs) - 2,
    right = Math.max(cx + w / 2, ...xs) + 2;
  const south = Math.min(cz - d / 2, ...zs) - 2,
    north = Math.max(cz + d / 2, ...zs) + 2;
  const scale = Math.min(493 / (right - left), 385 / (north - south));
  convert = ([x, z]) => [
    280 + (x - (left + right) / 2) * scale,
    224 - (z - (north + south) / 2) * scale,
  ];
  function line(a, b, style) {
    const [x1, y1] = convert(a),
      [x2, y2] = convert(b);
    return svgNode(svg, "line", { x1, y1, x2, y2, ...style });
  }
  function rect(center, size, style) {
    const [x, y] = convert([center[0] - size[0] / 2, center[1] + size[1] / 2]);
    return svgNode(svg, "rect", {
      x,
      y,
      width: size[0] * scale,
      height: size[1] * scale,
      ...style,
    });
  }
  function dot(p, r, style) {
    const [cx, cy] = convert(p);
    return svgNode(svg, "circle", { cx, cy, r, ...style });
  }
  svg.replaceChildren();
  for (let x = Math.ceil(left / 2) * 2; x <= right; x += 2)
    line([x, south], [x, north], { stroke: "#d9dece", "stroke-width": 0.7 });
  for (let z = Math.ceil(south / 2) * 2; z <= north; z += 2)
    line([left, z], [right, z], { stroke: "#d9dece", "stroke-width": 0.7 });
  rect(room.xz, room.size, {
    fill: "#f8f5e9",
    "fill-opacity": 0.86,
    stroke: "#677a69",
    "stroke-width": 2.2,
  });
  dot(room.xz, 4.5 * scale, {
    fill: "none",
    stroke: "#9b9674",
    "stroke-dasharray": "5 5",
  });
  dot(room.xz, 3 * scale, { fill: "#e7dfbb", stroke: "#918454" });
  const [ox, oy] = convert(room.xz);
  svgNode(
    svg,
    "text",
    {
      x: ox,
      y: oy + 4,
      "text-anchor": "middle",
      fill: "#655b32",
      "font-size": 11,
    },
    "KUND",
  );
  for (const c of activeMap.studyCovers.filter((c) => c.site === entry.site)) {
    const chosen = activeMarks.some((m) => m.cover.id === c.id);
    const shape = rect(c.center_xz, c.size_xz, {
      fill: c.collision === false ? "#ded5a5" : chosen ? "#416551" : "#a6af98",
      stroke: chosen ? "#203f32" : "#76826b",
      "stroke-width": chosen ? 1.8 : 1,
      "fill-opacity": c.collision === false ? 0.55 : 1,
    });
    svgNode(shape, "title", {}, c.label + " · " + short(c.height_m) + " m");
  }
  const [tx, ty] = convert(activeMarks[0].threat);
  svgNode(svg, "path", {
    d: `M${tx} ${ty - 7}l7 13h-14z`,
    fill: "#924628",
    stroke: "#fff7e4",
  });
  const [mx, my] = convert(entry.mouth_xz);
  svgNode(svg, "circle", {
    cx: mx,
    cy: my,
    r: 4,
    fill: "#eadeb4",
    stroke: "#4d6050",
    "stroke-width": 2,
  });
  activeMarks.forEach((m, i) => {
    line(m.hide, m.shoulder, { stroke: "#587b63", "stroke-width": 2 });
    line(m.shoulder, m.peek, {
      stroke: "#81452e",
      "stroke-width": 1.75,
      "stroke-dasharray": "3 3",
    });
    const [hx, hy] = convert(m.hide),
      [px, py] = convert(m.peek);
    if (distance(m.hide, m.shoulder) > 0.15)
      dot(m.shoulder, 2.8, {
        fill: "#d5ecbf",
        stroke: "#163e30",
        "stroke-width": 1,
      });
    dot(m.hide, 10, { fill: "#1c5847", stroke: "#fff8dd", "stroke-width": 2 });
    svgNode(
      svg,
      "text",
      {
        x: hx,
        y: hy + 3.6,
        "text-anchor": "middle",
        fill: "#fff",
        "font-size": 10,
        "font-weight": "bold",
      },
      i + 1,
    );
    svgNode(svg, "path", {
      d: `M${px} ${py - 5}l5 5-5 5-5-5z`,
      fill: "#fcf3d9",
      stroke: "#824128",
      "stroke-width": 1.6,
    });
  });
  svgNode(svg, "path", {
    d: "M32 42V21m-4 6 4-7 4 7",
    fill: "none",
    stroke: "#526757",
    "stroke-width": 1.6,
  });
  svgNode(
    svg,
    "text",
    { x: 32, y: 15, "text-anchor": "middle", fill: "#405446", "font-size": 10 },
    "N",
  );
  svgNode(svg, "path", {
    d: `M36 424v5h${5 * scale}v-5`,
    fill: "none",
    stroke: "#556550",
    "stroke-width": 1.7,
  });
  svgNode(
    svg,
    "text",
    { x: 36, y: 444, fill: "#405446", "font-size": 11 },
    "5 m",
  );
  svgNode(svg, "circle", {
    id: "actor-marker",
    r: 6.5,
    fill: "#cce9f3",
    stroke: "#255f8c",
    "stroke-width": 2.3,
    visibility: "hidden",
  });
  ui("sheet-title").textContent = room.label;
  ui("floor-label").textContent =
    short(w) + " × " + short(d) + " m · floor " + short(room.y) + " m";
  ui("entry-title").textContent = approach + " entrance";
  ui("entry-figures").textContent =
    short(entry.width_m) +
    " m wide · threshold (" +
    pointLabel(entry.mouth_xz) +
    ")";
  ui("pockets").replaceChildren();
  for (const [index, m] of activeMarks.entries()) {
    const box = document.createElement("div");
    box.className = "pocket";
    const title = document.createElement("strong");
    title.textContent = index + 1 + ". " + m.cover.label;
    const meta = document.createElement("p");
    meta.textContent =
      m.data.posture +
      " · " +
      short(m.cover.height_m) +
      " m high · hide (" +
      pointLabel(m.hide) +
      ")";
    const peeking = document.createElement("p");
    peeking.textContent =
      (m.data[prefix + "body_hide_xz"]
        ? "Shoulder (" + pointLabel(m.shoulder) + ") · "
        : "") +
      "Peek (" +
      pointLabel(m.peek) +
      ").";
    box.append(title, meta, peeking);
    if (!rev && Number.isInteger(m.data.visible_air_rays)) {
      const air = document.createElement("p");
      air.textContent =
        "At the shoulder mark, observer raised 4 m: " +
        m.data.visible_air_rays +
        " of 9 body samples visible.";
      box.append(air);
    }
    ui("pockets").append(box);
  }
  drawActor();
}
function drawActor() {
  if (!actor) return;
  const [x, y] = convert(actor),
    mark = ui("actor-marker");
  mark.setAttribute("cx", x);
  mark.setAttribute("cy", y);
  mark.setAttribute("visibility", "visible");
}
function walk() {
  actor = [...activeMarks[0].threat];
  walking = ground.canStand(actor);
  if (!walking) {
    actor = null;
    ui("walk-info").textContent = "This observer cannot be occupied.";
    return;
  }
  ui("walk").textContent = "Reset to observer";
  ui("walk-info").textContent =
    "Use arrow keys, WASD or the four direction buttons.";
  drawActor();
}
const walks = { north: [0, 1], south: [0, -1], east: [1, 0], west: [-1, 0] };
function moveActor(direction) {
  if (!walking) walk();
  if (!walking) return;
  const next = ground.move(
    actor,
    walks[direction].map((v) => v * 0.25),
  );
  const near = activeMarks.find((m) => distance(next, m.hide) < 0.42);
  const status = near
    ? "Near the " + near.cover.label + " whole-body hide mark."
    : distance(actor, next) < 0.01
      ? "A solid or floor edge blocks this step."
      : "Walking · (" + pointLabel(next) + ")";
  actor = next;
  drawActor();
  ui("walk-info").textContent = status;
}
let frameRequest = 0,
  traceAtTime;
function stopTrace() {
  cancelAnimationFrame(frameRequest);
  frameRequest = 0;
  ui("play-trace").textContent = "Play trace";
}
function playTrace() {
  if (frameRequest) {
    stopTrace();
    return;
  }
  const slider = ui("scrub");
  if (Number(slider.value) >= Number(slider.max)) traceAtTime(0);
  const initial = Number(slider.value),
    start = performance.now();
  ui("play-trace").textContent = "Pause trace";
  function frame(now) {
    const tick = Math.min(
      Number(slider.max),
      initial + Math.floor(((now - start) * field.rate) / 1000),
    );
    traceAtTime(tick);
    if (tick < Number(slider.max)) frameRequest = requestAnimationFrame(frame);
    else stopTrace();
  }
  frameRequest = requestAnimationFrame(frame);
}
function drawTrace() {
  stopTrace();
  const t = field.traces.find((t) => t.id === ui("trace").value),
    pts = t.points,
    rate = field.rate;
  const elev = ui("elevation"),
    plan = ui("trace-plan");
  elev.replaceChildren();
  plan.replaceChildren();
  const zMin = Math.min(0, ...pts.map((p) => p[3])),
    zMax = Math.max(zMin + 2, ...pts.map((p) => p[3])) + 0.25;
  const last = Math.max(1, ...pts.map((p) => p[0])),
    at = (tick, z) => [
      55 + (470 * tick) / last,
      210 - (174 * (z - zMin)) / (zMax - zMin),
    ];
  const line = (parent, a, b, style) =>
    svgNode(parent, "line", {
      x1: a[0],
      y1: a[1],
      x2: b[0],
      y2: b[1],
      ...style,
    });
  for (let y = Math.ceil(zMin); y <= Math.floor(zMax); y++) {
    let level = at(0, y)[1];
    line(elev, [55, level], [525, level], { stroke: "#c8d0bd" });
    svgNode(
      elev,
      "text",
      {
        x: 46,
        y: level + 4,
        "text-anchor": "end",
        "font-size": 12,
        fill: "#4f5d52",
      },
      y + " m",
    );
  }
  for (let i = 0; i <= 4; i++) {
    const tick = (last * i) / 4;
    const x = at(tick, 0)[0];
    line(elev, [x, 34], [x, 212], { stroke: "#d6dcca" });
    svgNode(
      elev,
      "text",
      { x, y: 235, "text-anchor": "middle", "font-size": 12, fill: "#4f5d52" },
      short(tick / rate) + " s",
    );
  }
  const ink = {
    fill: "none",
    stroke: "#246852",
    "stroke-width": 3.2,
    "stroke-linejoin": "round",
  };
  function path(parent, points) {
    svgNode(parent, "polyline", {
      points: points.map((p) => p.join(",")).join(" "),
      ...ink,
    });
    const [x, y] = points.at(-1);
    svgNode(parent, "path", {
      d: `M${x - 5} ${y - 5}l10 10m-10 0 10-10`,
      fill: "none",
      stroke: "#9b4128",
      "stroke-width": 2,
    });
  }
  path(
    elev,
    pts.map((p) => at(p[0], p[3])),
  );
  const xs = pts.map((p) => p[1]),
    ns_ = pts.map((p) => p[2]),
    a = Math.min(...xs),
    b = Math.max(...xs),
    c = Math.min(...ns_),
    d = Math.max(...ns_);
  const scale = Math.min(440 / Math.max(b - a, 1), 94 / Math.max(d - c, 1)),
    convertXY = (p) => [
      280 + (p[1] - (a + b) / 2) * scale,
      75 - (p[2] - (c + d) / 2) * scale,
    ];
  path(plan, pts.map(convertXY));
  const [sx, sy] = convertXY(pts[0]);
  svgNode(plan, "circle", {
    cx: sx,
    cy: sy,
    r: 3.5,
    fill: "#e4d188",
    stroke: "#263e2c",
  });
  svgNode(
    plan,
    "text",
    { x: 17, y: 25, fill: "#506456", "font-size": 11 },
    "↑ N",
  );
  svgNode(
    plan,
    "text",
    { x: 17, y: 139, fill: "#506456", "font-size": 11 },
    "Horizontal extent " + short(b - a) + " × " + short(d - c) + " m",
  );
  const makeCursor = (svg) =>
    svgNode(svg, "circle", {
      r: 5.3,
      fill: "#ffde85",
      stroke: "#654721",
      "stroke-width": 2,
    });
  const sectionCursor = makeCursor(elev),
    planCursor = makeCursor(plan);
  ui("scrub").max = t.ticks;
  traceAtTime = (tick) => {
    const sample = pts.findLast((p) => p[0] <= tick) || pts[0];
    const place = (cursor, xy) => {
      cursor.setAttribute("cx", xy[0]);
      cursor.setAttribute("cy", xy[1]);
    };
    place(sectionCursor, at(tick, sample[3]));
    place(planCursor, convertXY(sample));
    ui("scrub").value = tick;
    ui("playhead").textContent = short(tick / rate) + " s · tick " + tick;
  };
  traceAtTime(0);
  ui("trace-title").textContent = t.title;
  ui("trace-kind").textContent =
    t.hero + " · " + (t.site === "b" ? "B" : t.site === "a" ? "A" : "District");
  ui("trace-result").textContent =
    t.verdict + " · " + short(t.ticks / rate) + " s";
  ui("events").replaceChildren(
    ...t.events.map((e) => {
      const li = document.createElement("li");
      li.textContent =
        short(e.tick / rate) +
        " s · " +
        e.type +
        (e.id ? " · " + e.id : "") +
        " · (" +
        pointLabel(e.xyz) +
        ")";
      return li;
    }),
  );
}
options(
  ui("district"),
  field.maps.map((p) => [p.id, p.title]),
);
pickDistrict();
options(
  ui("trace"),
  field.traces.map((t) => [t.id, t.hero + " · " + t.title]),
);
drawTrace();
for (const [id, action] of Object.entries({
  district: pickDistrict,
  court: pickCourt,
  door: pickDoor,
  face: pickDoor,
  trace: drawTrace,
}))
  ui(id).addEventListener("change", action);
ui("walk").addEventListener("click", walk);
ui("play-trace").addEventListener("click", playTrace);
ui("scrub").addEventListener("input", () => {
  stopTrace();
  traceAtTime(Number(ui("scrub").value));
});
for (const b of document.querySelectorAll("[data-step]"))
  b.addEventListener("click", () => moveActor(b.dataset.step));
const bindings = {
  ArrowUp: "north",
  ArrowDown: "south",
  ArrowLeft: "west",
  ArrowRight: "east",
  w: "north",
  s: "south",
  a: "west",
  d: "east",
};
function withinDrill() {
  return (
    document.activeElement?.closest("#courts") &&
    ui("plan").getBoundingClientRect().bottom > 10
  );
}
document.addEventListener("keydown", (event) => {
  if (
    walking &&
    withinDrill() &&
    bindings[event.key] &&
    !event.target.closest("select,input,textarea") &&
    !event.ctrlKey &&
    !event.metaKey &&
    !event.altKey
  ) {
    event.preventDefault();
    moveActor(bindings[event.key]);
  }
});
