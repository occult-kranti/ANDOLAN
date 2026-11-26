import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { GroundPlan, Rehearsal } from "./engine.mjs";

const page = readFileSync(new URL("../rehearsal.html",import.meta.url),"utf8");
const {maps,rules} = JSON.parse(page.match(/<script type="application\/json" id="atlas-data">(.*?)<\/script>/s)[1]);
const plans = Object.fromEntries(maps.map(map=>[map.id,new GroundPlan(map)]));
const dist = (a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
const ticks = (run,n,input={})=>{for(let i=0;i<n;i++)run.step(input);};

function walkTo(run,waypoint){
  const limit=Math.ceil(dist(run.position,waypoint)*rules.hz/rules.speed*1.5)+30;
  for(let i=0;i<limit && dist(run.position,waypoint)>.135;i++){
    const [x,z]=waypoint.map((v,k)=>v-run.position[k]);
    run.step({x,z});
  }
  assert.ok(dist(run.position,waypoint)<=.135,
    `${run.plan.data.title} stopped at ${run.position} approaching ${waypoint}`);
}

test("each role can walk from its spawn to each site on all four dry layouts",()=>{
  let runs=0;
  for(const plan of Object.values(plans)){
    for(const start of ["atk","def"])for(const end of ["a","b"]){
      const run=new Rehearsal(plan,rules,"explore",start,end);
      const [estimate,steps]=plan.data.guides[`dry:${start}:${end}`];
      for(const [index,forward] of steps){
        const link=plan.links[index];
        assert.ok(["walk","ramp"].includes(link.kind));
        const pts=forward?link.points:[...link.points].reverse();
        for(const p of pts.slice(1))walkTo(run,p);
      }
      assert.equal(plan.siteAt(run.position,rules.siteRadius),end);
      assert.ok(Math.abs(run.elapsed/rules.hz-estimate)<2.0,plan.data.title);
      runs++;
    }
  }
  assert.equal(runs,16);
});

test("wet walking, radius-sensitive cover, floor edges and diagonal speed",()=>{
  const plan=plans.mandala;
  const wet=new Rehearsal(plan,rules,"explore","ford");
  const wetOrigin=[...wet.position];
  wet.step({x:1,z:1});
  assert.ok(Math.abs(dist(wetOrigin,wet.position)-rules.speed*rules.water/rules.hz)<1e-6);
  const dry=new Rehearsal(plan,rules);
  const origin=[...dry.position];dry.step({x:1,z:1});
  assert.ok(Math.abs(dist(origin,dry.position)-rules.speed/rules.hz)<1e-6);
  assert.equal(plan.canStand([0,-200]),false);
  const c=plan.data.cover[0], edge=[c.xz[0]+c.size[0]/2,c.xz[1]];
  assert.equal(plan.canStand(edge),false);
  assert.equal(plan.canStand([edge[0]+.44,edge[1]]),false);
  const legal=[edge[0]+.46,edge[1]];
  assert.equal(plan.canStand(legal),true);
  assert.deepEqual(plan.move(legal,[-.25,0]),legal);
});

test("fold windups are interruptible, clockwise and exactly invertible",()=>{
  const plan=plans.mandala;
  for(const edge of plan.folds){
    const run=new Rehearsal(plan,rules,"explore",edge.from);
    run.step({x:1,z:1});run.step({x:1,z:0});
    const from=[...run.position],face=[...run.facing], n=edge.seconds*rules.hz;
    ticks(run,n-1,{hold:true});
    assert.deepEqual(run.position,from);
    run.step();
    assert.equal(run.progress,0);
    ticks(run,n,{hold:true});
    const before=plan.data.nodes[edge.from].xz,after=plan.data.nodes[edge.to].xz;
    const dx=from[0]-before[0],dz=from[1]-before[1];
    assert.equal(Math.abs(edge.quarter_turns),1);
    assert.ok(dist(run.position,[after[0]+dz*edge.quarter_turns,after[1]-dx*edge.quarter_turns])<1e-7);
    assert.ok(dist(run.facing,[face[1]*edge.quarter_turns,-face[0]*edge.quarter_turns])<1e-7);
    const arrival=[...run.position];ticks(run,n+5,{hold:true});assert.deepEqual(run.position,arrival);
    run.step();
    const reverseSign=run.availableAction().name;
    assert.ok(reverseSign.includes(edge.quarter_turns===1?"Left turn":"Right turn"));
    assert.ok(reverseSign.endsWith(plan.data.nodes[edge.from].label));
    ticks(run,n,{hold:true});
    assert.ok(run.message.startsWith(reverseSign));
    assert.ok(dist(run.position,from)<1e-7);
    assert.ok(dist(run.facing,face)<1e-7);
  }
});

test("blocked fold exit keeps the runner on the source ground",()=>{
  const data=structuredClone(plans.mandala.data),gate=data.links.find(l=>l.kind==="fold");
  data.cover.push({xz:data.nodes[gate.to].xz,size:[1.6,1.6],height:1.5,label:"test obstacle"});
  const run=new Rehearsal(new GroundPlan(data),rules,"explore",gate.from),p=[...run.position];
  ticks(run,gate.seconds*rules.hz,{hold:true});
  assert.deepEqual(run.position,p);
  assert.match(run.message,/obstructed/);
});

test("either site can be kindled off-centre and the exact vessel governs the retake",()=>{
  for(const plan of Object.values(plans))for(const site of ["a","b"]){
    const run=new Rehearsal(plan,rules,"carry",site);
    ticks(run,8,{x:1}); // 2 m east of the centre, outside its 1.5 m interaction radius.
    const planted=[...run.position];
    ticks(run,rules.kindle-1,{hold:true});
    assert.equal(run.phase,"approach");
    run.step({hold:true});
    assert.equal(run.phase,"handoff");assert.deepEqual(run.vessel,planted);
    run.takeDefence();assert.equal(run.phase,"burn");assert.deepEqual(run.vessel,planted);
    assert.equal(run.remaining,rules.burn);
    const [_,steps]=plan.data.guides[`dry:${run.start}:${site}`];
    for(const [idx,forward] of steps){
      const pts=plan.links[idx].points;
      for(const p of (forward?pts:[...pts].reverse()).slice(1))walkTo(run,p);
    }
    assert.equal(run.availableAction(),null);
    walkTo(run,planted);
    ticks(run,rules.quench-1,{hold:true});
    assert.equal(run.phase,"burn");
    run.step({hold:true});
    assert.equal(run.phase,"ended");assert.match(run.message,/Quenched/);
  }
});

test("recovery, release, accepted-hit interruption and final tick ordering",()=>{
  const run=new Rehearsal(plans.lanka,rules,"carry","a");
  run.drop();assert.deepEqual(run.vessel,run.position);assert.equal(run.carrying,false);
  ticks(run,12,{x:1});assert.equal(run.availableAction(),null);
  ticks(run,12,{x:-1});run.step({hold:true});
  assert.equal(run.carrying,true);assert.equal(run.channel,null);
  ticks(run,2,{hold:true});assert.equal(run.progress,0);
  run.step();ticks(run,15,{hold:true});assert.equal(run.progress,15);
  run.interrupt();ticks(run,5,{hold:true});assert.equal(run.progress,0);
  run.step();
  ticks(run,run.remaining-rules.kindle);
  ticks(run,rules.kindle,{hold:true});assert.equal(run.phase,"handoff");
  const defender=new Rehearsal(plans.ayodhya,rules,"retake","a","a");
  ticks(defender,8,{z:1});ticks(defender,defender.remaining-rules.quench);
  ticks(defender,rules.quench,{hold:true});assert.match(defender.message,/Quenched/);
  for(const mode of ["carry","retake"]){
    const timeout=new Rehearsal(plans.ayodhya,rules,mode);
    timeout.step({x:1});ticks(timeout,timeout.remaining);
    assert.equal(timeout.phase,"ended");
    const ended=structuredClone(timeout.position);
    ticks(timeout,100,{x:1,hold:true});assert.deepEqual(timeout.position,ended);
  }
});

function buildingAxes(plan) {
  const spec = plan.data.architecture;
  const [cx, cz] = plan.data.nodes[spec.node].xz;
  const angle = spec.axis_deg * Math.PI / 180, c = Math.cos(angle), s = Math.sin(angle);
  return {
    world: (x, y) => [cx + c*x + s*y, cz - s*x + c*y],
    local: ([x,z]) => [(x-cx)*c - (z-cz)*s, (x-cx)*s + (z-cz)*c],
    across: side => ({x: c*side, z: -s*side})
  };
}

test("both masonry banks block the body while centre and shoulder crossings stay open", () => {
  for (const plan of Object.values(plans)) {
    const spec = plan.data.architecture, axes = buildingAxes(plan);
    const [, depth] = spec.footprint, shoulder = spec.opening / 2 - .65;
    for (const offset of [-shoulder, 0, shoulder]) {
      const run = new Rehearsal(plan, rules, "explore", spec.node);
      for (const point of [[offset,0], [offset,-depth/2-.20], [offset,depth/2+.20], [offset,-depth/2-.20]]) {
        walkTo(run, axes.world(...point));
        assert.notEqual(plan.surface(run.position).kind, "water", spec.name + " has a dry passage");
      }
    }
    for (const side of [-1, 1]) {
      const solids = plan.masonry.map(piece => piece.ring.map(axes.local));
      const nearest = solids.filter(polygon => polygon.every(([x]) => x * side > 0))
        .sort((a,b) => Math.min(...a.map(([x]) => Math.abs(x))) - Math.min(...b.map(([x]) => Math.abs(x))))[0];
      // Test an actual broad blocker. A decorative inlay can be less than a finger wide.
      const bank = nearest.some(p => Math.abs(p[1] - nearest[0][1]) > .45) ? nearest :
        solids.find(ring => ring.every(([x]) => x*side > 0) && Math.max(...ring.map(p=>p[1]))-Math.min(...ring.map(p=>p[1])) > 1);
      const face = Math.min(...bank.map(([x]) => Math.abs(x)));
      const y = bank.reduce((sum,p) => sum + p[1], 0) / bank.length;
      const run = new Rehearsal(plan, rules, "explore", spec.node);
      walkTo(run, axes.world(0, y));
      ticks(run, 40, axes.across(side));
      const gap = face - Math.abs(axes.local(run.position)[0]);
      assert.ok(gap >= .449 && gap <= .71, spec.name + " bank clearance " + gap);
      const contact = [...run.position]; ticks(run, 8, axes.across(side));
      assert.deepEqual(run.position, contact);
    }
  }
});

test("the authored approaches clear each building and the well's basins leave a dry sill", () => {
  let traversals = 0;
  for (const plan of Object.values(plans)) {
    const host = plan.data.architecture.node;
    for (const link of plan.links.filter(e => e.kind !== "fold" && (e.from === host || e.to === host))) {
      for (const forward of [true, false]) {
        const run = new Rehearsal(plan, rules, "explore", forward ? link.from : link.to);
        const path = forward ? link.points : [...link.points].reverse();
        for (const point of path.slice(1)) walkTo(run, point);
        traversals++;
      }
    }
  }
  assert.equal(traversals,18);
  const well = plans.ayodhya;
  assert.equal(well.basins.length, 2);
  for (const {ring} of well.basins) {
    const centre = [0,1].map(k => ring.reduce((sum, p) => sum + p[k], 0) / ring.length);
    assert.ok(well.canStand(centre));
    assert.equal(well.surface(centre).kind, "water");
  }
  assert.notEqual(well.surface(well.data.nodes.well.xz).kind, "water");
  const gallery = plans.lanka, galleryAxes = buildingAxes(gallery);
  assert.equal(gallery.masonry.length, 8);
  const gap = new Rehearsal(gallery, rules, "explore", gallery.data.architecture.node);
  walkTo(gap, galleryAxes.world(4.65,0));
  assert.ok(galleryAxes.local(gap.position)[0] > 4.5, "Can walk between actual gallery pillars");
});
