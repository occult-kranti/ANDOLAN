const {maps, rules} = JSON.parse(document.getElementById("atlas-data").textContent);
const byId = id => document.getElementById(id);
const planCanvas = byId("plan");
const xmlns = "http://www.w3.org/2000/svg";
const markerLabels = {atk:"AT", def:"DF", a:"A", b:"B", mid:"M"};
const landmarkArt = {
  mandala:["Ghat bell comb","0% 0%"], lanka:["Split harbour beacon","100% 0%"],
  ayodhya:["Twin mooring drums","0% 100%"], kurukshetra:["Wind fork","100% 100%"]
};
const vectors = {up:[0,1], right:[1,0], down:[0,-1], left:[-1,0]};
const bindings = {KeyW:"up", ArrowUp:"up", KeyA:"left", ArrowLeft:"left",
  KeyS:"down", ArrowDown:"down", KeyD:"right", ArrowRight:"right", KeyE:"hold"};
const held = new Map();
const setText = (id, text) => {
  const element = byId(id);
  if (element.textContent !== text) element.textContent = text;
};
function svg(group, type, attrs) {
  const child = document.createElementNS(xmlns,type);
  for (const [key, value] of Object.entries(attrs)) child.setAttribute(key, value);
  group.append(child);
  return child;
}
function options(select, pairs) {
  select.replaceChildren(...pairs.map(([value, label]) => new Option(label, value)));
}
function shapePath(edge, forward = true) {
  const coords = forward ? edge.points : [...edge.points].reverse();
  return coords.map(([x,z],i) => (i ? "L" : "M") + x + " " + -z).join(" ");
}
function rectAttrs({xz:[x,z], size:[w,d]}) {
  return {x:x-w/2,y:-z-d/2,width:w,height:d};
}
let plan, session, mapId, goal, follow = false, paused = false;
let lastTime = null, lag = 0, scale = 1;
const seenKeys = new Set();
const mapButtons = new Map();
for (const map of maps) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = map.title;
  button.addEventListener("click", () => {
    if (mapId !== map.id) loadMap(map.id);
  });
  byId("districts").append(button);
  mapButtons.set(map.id, button);
}

function drawPlan() {
  const floors = byId("floors"), marks = byId("marks"), labels = byId("labels");
  floors.replaceChildren(); marks.replaceChildren(); labels.replaceChildren();
  const physical = plan.links.filter(e => e.kind !== "fold");
  for (const outline of [true,false]) {
    for (const edge of physical) {
      svg(floors,"path",{d:shapePath(edge),fill:"none",stroke:outline?"#64776b":"#dccca6",
        "stroke-width":edge.width+(outline ? .8 : 0),"stroke-linejoin":"round","stroke-linecap":"round"});
    }
    for (const [,room] of plan.rooms) svg(floors,"rect",{...rectAttrs(room),fill:"#dccca6",
      stroke:outline?"#64776b":"none","stroke-width":.8});
  }
  for (const edge of physical) {
    if (edge.kind === "water") svg(floors,"path",{d:shapePath(edge),fill:"none",stroke:"url(#wet)",
      "stroke-width":edge.width,"stroke-linecap":"round","stroke-linejoin":"round"});
    if (edge.kind === "ramp") svg(floors,"path",{d:shapePath(edge),fill:"none",stroke:"#65815e",
      "stroke-width":.55,"stroke-dasharray":"1.7 1.1"});
  }
  for (const [id, room] of plan.rooms)
    svg(floors,"rect",{...rectAttrs(room),fill:plan.wetRooms.has(id)?"url(#wet)":"#e5d8b9"});
  const study = plan.data.building;
  const points = ring => ring.map(([x, z]) => x + "," + -z).join(" ");
  svg(floors, "polygon", {points: points(study.outline), fill: "none", stroke: "#986e44",
    "stroke-width": .35, "stroke-dasharray": ".7 .38"});
  svg(floors, "polygon", {points: points(study.passage), fill: "#f1dec1", stroke: "none"});
  for (const basin of study.water) {
    const surface = svg(floors, "polygon", {points: points(basin.ring), fill: "url(#wet)"});
    svg(surface, "title", {}).textContent = plan.data.architecture.name + " · stepped basin";
  }
  for (const piece of study.solids) {
    const block = svg(marks, "polygon", {points: points(piece.ring), fill: "url(#stone)",
      stroke: "#573d34", "stroke-width": .19, "data-masonry": piece.label});
    svg(block, "title", {}).textContent = plan.data.architecture.name + " · " + piece.label;
  }
  for (const gate of plan.folds) {
    const track = svg(marks, "path", {d:shapePath(gate),stroke:"#d3a2ce",
      "stroke-width":.7,"stroke-dasharray":"1.9 1.1",fill:"none"});
    svg(track,"title",{}).textContent = gate.cue;
    for (const id of [gate.from,gate.to]) {
      const [x,z] = plan.data.nodes[id].xz;
      svg(marks,"path",{d:"M0 -2.3 2.3 0 0 2.3 -2.3 0 Z",transform:"translate("+x+" "+ -z+")",
        fill:"#7c537b",stroke:"#edd7e9","stroke-width":.4});
    }
  }
  for (const cover of plan.data.cover) {
    const obj = svg(marks,"rect",{...rectAttrs(cover),fill:"url(#solid)",stroke:"#233b32","stroke-width":.32});
    svg(obj,"title",{}).textContent=cover.label+" · "+cover.height+" m";
  }
  for (const [id, room] of plan.rooms) {
    const [x,z]=room.xz;
    if(id==="a" || id==="b") {
      svg(marks,"circle",{cx:x,cy:-z,r:rules.siteRadius,fill:"none",stroke:"#963d23","stroke-width":.55});
      svg(marks,"circle",{cx:x,cy:-z,r:rules.siteRadius+rules.reach,fill:"none",stroke:"#92583d",
        "stroke-width":.26,"stroke-dasharray":".6 .65"});
    }
    if (id in markerLabels) {
      const t=svg(labels,"text",{"data-room":id,class:"map-label",x,y:-z,"text-anchor":"middle"});
      t.textContent=(id==="a" || id==="b" ? id.toUpperCase()+" · " : "") + room.label;
    } else {
      const dot=svg(marks,"circle",{cx:x,cy:-z,r:.68,fill:"#637961"});
      svg(dot,"title",{}).textContent=room.label;
    }
  }
}

function frameMap() {
  const [l,s,r,n] = plan.data.bounds;
  const width=planCanvas.clientWidth || 500, height=planCanvas.clientHeight || 420;
  const aspect=width/height;
  const vh=follow?55:Math.max(n-s+22,(r-l+25)/aspect);
  const vw=vh*aspect;
  const center=follow?session.position:[(l+r)/2,(s+n)/2];
  scale=height/vh;
  planCanvas.setAttribute("viewBox",[center[0]-vw/2,-center[1]-vh/2,vw,vh].join(" "));
  for (const t of byId("labels").children) {
    const id=t.dataset.room;
    const [x,z]=plan.data.nodes[id].xz;
    const off = id==="a"?-7:id==="b"?7:0;
    t.setAttribute("x",x+off);
    const vertical = id==="atk"?7:id==="def"?-7:id==="mid"?-7:0;
    t.setAttribute("y",-z+vertical+3/scale);
    t.setAttribute("text-anchor",id==="a"?"end":id==="b"?"start":"middle");
    t.setAttribute("font-size",(follow?12:11)/scale);
    // In narrow views a site caption can run off the sheet. Keep it with its visible site.
    const left = center[0] - vw / 2 + 5 / scale, right = center[0] + vw / 2 - 5 / scale;
    if ((id === "a" || id === "b") && x >= left && x <= right) {
      const bounds = t.getBBox();
      if (bounds.x < left || bounds.x + bounds.width > right) {
        const half = bounds.width / 2;
        t.setAttribute("text-anchor", "middle");
        t.setAttribute("x", Math.max(left + half, Math.min(right - half, x)));
        t.setAttribute("y", -z - 5 - 1 / scale);
      }
    }
  }
  const length=follow?5:20;
  setText("scale",length+" m");
  byId("scale").style.width=(length*scale)+"px";
}

function clearInput() {
  held.clear(); seenKeys.clear(); lag=0; lastTime=null;
  if (session) session.stopChannel();
  document.querySelectorAll("button.active").forEach(b=>b.classList.remove("active"));
}
function updateGuide() {
  const gallery=byId("guide-layer");
  gallery.replaceChildren();
  const route=plan.data.guides[[byId("profile").value,session.start,goal].join(":")];
  if (!route) {
    setText("route",session.start===goal?"You start at the selected destination.":"This selection has no route with those crossings.");
    setText("estimate",""); return;
  }
  const [seconds,steps]=route;
  const names=[plan.data.nodes[session.start].label];
  for (const [idx,forward] of steps) {
    const edge=plan.links[idx];
    svg(gallery,"path",{d:shapePath(edge,forward),fill:"none",stroke:"#89522b",
      "stroke-width":1.05,"stroke-dasharray":"1.6 .95","stroke-linecap":"round"});
    names.push(plan.data.nodes[forward?edge.to:edge.from].label);
  }
  setText("route",names.join(" → "));
  setText("estimate",seconds.toFixed(1)+" s · uninterrupted route estimate");
}
function configureStarts() {
  options(byId("start"),plan.rooms.map(([id,r])=>
    [id,r.label+(id==="atk"?" · Attack spawn":id==="def"?" · Defence spawn":"")]));
}
function configureGoals(preferred) {
  const retake = byId("mode").value==="retake";
  const ids=retake?["a","b"]:[...new Set(["a","b","mid",...plan.folds.flatMap(e=>[e.from,e.to])])];
  options(byId("goal"),ids.map(id=>[id,(id==="a"||id==="b"?id.toUpperCase()+" · ":"")+plan.data.nodes[id].label]));
  goal=ids.includes(preferred)?preferred:"a";
  byId("goal").value=goal;
  setText("goal-caption",retake?"Lit site":"Guide to");
}
function restart() {
  clearInput();
  session=new Rehearsal(plan,rules,byId("mode").value,byId("start").value,goal);
  paused=false;
  updateGuide();frameMap();drawActor();
}
function chooseExercise(preferredGoal) {
  configureGoals(preferredGoal);
  byId("start").value=byId("mode").value==="retake"?(goal==="a"?"b":"a"):"atk";
  restart();
}
function loadMap(id, preferredGoal) {
  mapId=id;
  plan=new GroundPlan(maps.find(m=>m.id===id));
  for(const [key,button] of mapButtons) button.setAttribute("aria-pressed",String(key===id));
  const map=plan.data;
  setText("district-name",map.title); setText("district-place",map.subtitle);
  const study=map.architecture;
  setText("landmark-name",study.name);
  setText("landmark-cue",study.play);
  setText("district-decision",map.decision);
  const [caption,position]=landmarkArt[id];
  byId("art").style.backgroundPosition=position;
  byId("art").setAttribute("aria-label",caption+" concept in "+map.title);
  setText("art-caption",caption);
  configureStarts();
  drawPlan();
  chooseExercise(preferredGoal);
}
function takeDefence() {
  if(session.phase!=="handoff")return;
  clearInput();
  session.takeDefence();
  byId("mode").value="retake";
  byId("start").value=session.start;
  configureGoals(session.target);
  paused=false;
  updateGuide();frameMap();drawActor();
}
function drawActor() {
  const [x,z]=session.position;
  const heading=Math.atan2(session.facing[0],session.facing[1])*180/Math.PI;
  byId("player").setAttribute("transform","translate("+x+" "+ -z+") rotate("+heading+")");
  const marker=session.vessel;
  byId("vessel").setAttribute("display",marker?"inline":"none");
  if(marker)byId("vessel").setAttribute("transform","translate("+marker[0]+" "+ -marker[1]+")");
  const surface=plan.surface(session.position);
  setText("position",surface.label+(surface.kind==="water"?" · Shallows":""));
  const explore=session.phase==="explore";
  setText("time-title",explore?"Route time":(session.mode==="carry" && session.phase!=="handoff")?"Approach remaining":"Fire clock");
  const clock=explore?session.elapsed:session.remaining;
  const time=Math.max(0,clock/rules.hz);
  setText("clock",Math.floor(time/60)+":"+String(Math.floor(time%60)).padStart(2,"0")+"."+Math.floor(time*10+1e-8)%10);
  const action=session.availableAction();
  setText("interact",action?((action.kind==="recover"?"":"Hold · ")+action.name):"Interact");
  const inHandoff=session.phase==="handoff", ended=session.phase==="ended";
  byId("handoff").hidden=!inHandoff;
  byId("drop").hidden=session.mode!=="carry" || !session.carrying;
  byId("drop").disabled=paused;
  byId("interrupt").disabled=paused || ended || inHandoff;
  byId("interact").disabled=paused || ended || inHandoff;
  byId("pause").disabled=ended || inHandoff;
  setText("pause",paused?"Resume":"Pause");
  const total=session.channel?.duration ?? 1;
  byId("progress").value=session.progress/total;
  setText("progress-text",session.channel?Math.round(session.progress*100/total)+"%":paused?"Paused":"Ready");
  setText("status",session.channel ? session.channel.name+" · keep holding." : session.message);
}
function step() {
  const values=new Set(held.values());
  let x=0,z=0;
  for(const direction of values) {
    if(vectors[direction]) {x+=vectors[direction][0];z+=vectors[direction][1];}
  }
  session.step({x,z,hold:values.has("hold")});
}
function frame(stamp) {
  if(lastTime!==null && !paused && !document.hidden) {
    lag+=Math.min(stamp-lastTime,250);
    const interval=1000/rules.hz;
    if(lag>=interval) {
      while(lag>=interval){step();lag-=interval;}
      if(follow)frameMap();
      drawActor();
    }
  }
  lastTime=stamp;
  requestAnimationFrame(frame);
}
function togglePause() {
  if (session.phase==="ended" || session.phase==="handoff") return;
  clearInput();paused=!paused;drawActor();
}
function heldButton(button,action) {
  const pressTick=new Map();
  const id=event=>"pointer-"+event.pointerId;
  button.addEventListener("pointerdown",event=>{
    if(event.button!==0 || button.disabled) return;
    event.preventDefault(); button.focus({preventScroll:true});
    button.setPointerCapture(event.pointerId);
    pressTick.set(event.pointerId,session.elapsed);
    held.set(id(event),action);button.classList.add("active");
  });
  const release=event=>{
    const shortTap=event.type==="pointerup" && held.has(id(event)) &&
      pressTick.get(event.pointerId)===session.elapsed;
    held.delete(id(event));pressTick.delete(event.pointerId);
    if(shortTap && vectors[action] && !paused){
      session.step({x:vectors[action][0],z:vectors[action][1]});drawActor();
    }
    if(![...held.values()].includes(action))button.classList.remove("active");
  };
  for(const type of ["pointerup","pointercancel","lostpointercapture"]) button.addEventListener(type,release);
  button.addEventListener("keydown",event=>{
    if(!["Space","Enter"].includes(event.code))return;
    event.preventDefault();
    if(!button.disabled){held.set(event.code,action);button.classList.add("active");}
  });
  button.addEventListener("keyup",event=>{
    if(!["Space","Enter"].includes(event.code))return;
    event.preventDefault();held.delete(event.code);button.classList.remove("active");
  });
  button.addEventListener("blur",()=>{held.delete("Space");held.delete("Enter");button.classList.remove("active");});
  // Assistive activation may emit a click without a pointer or key hold.
  button.addEventListener("click",event=>{
    if(event.detail!==0 || button.disabled || paused)return;
    if(action==="hold"){
      if(held.has("assist-hold"))held.delete("assist-hold");else held.set("assist-hold","hold");
    }else if(!held.size){
      session.step({x:vectors[action][0],z:vectors[action][1]});drawActor();
    }
  });
}
for(const button of document.querySelectorAll("[data-direction]")) heldButton(button,button.dataset.direction);
heldButton(byId("interact"),"hold");
document.addEventListener("keydown",event=>{
  if(event.altKey||event.ctrlKey||event.metaKey||event.target.closest?.("input,select,textarea,summary"))return;
  const action=bindings[event.code];
  if(!action && event.code!=="KeyP" && event.code!=="KeyG")return;
  event.preventDefault();
  if(event.repeat || seenKeys.has(event.code))return;
  seenKeys.add(event.code);
  if(event.code==="KeyP"){togglePause();return;}
  if(paused)return;
  if(event.code==="KeyG"){session.drop();drawActor();return;}
  held.set(event.code,action);
});
document.addEventListener("keyup",event=>{held.delete(event.code);seenKeys.delete(event.code);});
function suspend(){
  clearInput();
  if(session?.started && !["ended","handoff"].includes(session.phase))paused=true;
  if(session)drawActor();
}
window.addEventListener("blur",suspend);
document.addEventListener("visibilitychange",()=>{if(document.hidden)suspend();});
byId("reset").addEventListener("click",restart);
byId("mode").addEventListener("change",()=>chooseExercise("a"));
byId("start").addEventListener("change",restart);
byId("goal").addEventListener("change",()=>{
  goal=byId("goal").value;
  if(byId("mode").value==="retake")restart();else updateGuide();
});
byId("profile").addEventListener("change",updateGuide);
byId("drop").addEventListener("click",()=>{session.drop();drawActor();});
byId("interrupt").addEventListener("click",()=>{session.interrupt();drawActor();});
byId("pause").addEventListener("click",togglePause);
byId("handoff").addEventListener("click",takeDefence);
byId("zoom").addEventListener("click",()=>{
  follow=!follow;
  byId("zoom").setAttribute("aria-pressed",String(follow));frameMap();
});
planCanvas.addEventListener("pointerdown",()=>planCanvas.focus({preventScroll:true}));
const query=new URLSearchParams(location.search);
if(["explore","carry","retake"].includes(query.get("exercise")))byId("mode").value=query.get("exercise");
loadMap(mapButtons.has(query.get("map"))?query.get("map"):maps[0].id,query.get("site"));
new ResizeObserver(frameMap).observe(planCanvas);
requestAnimationFrame(frame);
