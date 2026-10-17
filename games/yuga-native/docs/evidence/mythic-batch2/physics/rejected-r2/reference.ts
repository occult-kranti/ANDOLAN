/** Original bounded convex-query reference. It is not the browser movement solver. */
import {readFileSync, writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {pathToFileURL} from 'node:url';
export type Vec = [number, number, number];
type Collider = {id:string,shape:'box'|'convex',center?:Vec,size?:Vec,vertices?:Vec[],faces?:number[][],layer:number,visual_only:boolean};
export type Query = {id:string,actor:string,kind:'ray'|'aim'|'sweep'|'overlap',mask:number,from?:Vec,to?:Vec,feet?:Vec,size?:Vec,motion?:Vec,origin?:Vec,yaw?:number,pitch?:number,distance?:number};
export type Fixture = {schema_version:number,fixture_id:string,coordinates:Record<string,string>,layers:Record<string,number>,query_contract:Record<string,unknown>,colliders:Collider[],queries:Query[],paired_stream:{id:string,tick_hz:number,ticks:number,mask:number,actors:{id:string,feet:Vec,velocity:Vec}[],support_drop_m:number}};
const add=(a:Vec,b:Vec):Vec=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]];
const sub=(a:Vec,b:Vec):Vec=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
const mul=(v:Vec,s:number):Vec=>[v[0]*s,v[1]*s,v[2]*s];
const dot=(a:Vec,b:Vec)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const cross=(a:Vec,b:Vec):Vec=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const length=(a:Vec)=>Math.hypot(...a);
const axes:Vec[]=[[1,0,0],[0,1,0],[0,0,1]];
const EPS=1e-8;
const finite=(x:unknown)=>typeof x==='number'&&Number.isFinite(x)&&Math.abs(x)<=10000;
const vec=(v:unknown):v is Vec=>Array.isArray(v)&&v.length===3&&v.every(finite);
const object=(v:unknown):v is Record<string,any>=>!!v&&typeof v==='object'&&!Array.isArray(v);
function require_(ok:unknown,reason:string):asserts ok {if(!ok)throw new Error(reason);}
export function validateFixture(raw:unknown):Fixture {
 require_(object(raw)&&raw.schema_version===1&&raw.fixture_id==='yuga-stacked-physics-v1','fixture identity');
 require_(object(raw.coordinates)&&raw.coordinates.units==='metres'&&raw.coordinates.up==='+Y'&&raw.coordinates.forward==='+Z'&&raw.coordinates.position==='feet_origin','coordinates');
 require_(object(raw.layers)&&raw.layers.world===1&&raw.layers.actor===2&&raw.layers.target===4,'layers');
 require_(object(raw.query_contract)&&raw.query_contract.actor_shape==='axis_aligned_box'&&vec(raw.query_contract.actor_size)&&raw.query_contract.actor_size.every((n:number)=>n>0)&&raw.query_contract.shape_margin===0,'query contract');
 require_(Array.isArray(raw.colliders)&&raw.colliders.length>0&&raw.colliders.length<=128,'collider bound');
 const ids=new Set<string>();
 for(const c of raw.colliders){
  require_(object(c)&&typeof c.id==='string'&&/^[a-z][a-z0-9-]{0,63}$/.test(c.id)&&!ids.has(c.id),'collider identity');ids.add(c.id);
  require_([1,2,4].includes(c.layer)&&typeof c.visual_only==='boolean','collider layer/visual tag');
  if(c.shape==='box')require_(vec(c.center)&&vec(c.size)&&c.size.every((n:number)=>n>0),'box shape');
  else {require_(c.shape==='convex'&&Array.isArray(c.vertices)&&c.vertices.length>=4&&c.vertices.length<=64&&c.vertices.every(vec),'convex vertices');require_(Array.isArray(c.faces)&&c.faces.length>=4&&c.faces.length<=64&&c.faces.every((f:unknown)=>Array.isArray(f)&&f.length>=3&&f.length<=64&&f.every((i:unknown)=>Number.isInteger(i)&&Number(i)>=0&&Number(i)<c.vertices.length)),'convex faces');
   const p=poly(c as Collider);require_(p.planes.every(pl=>length(pl.normal)>.99&&p.vertices.every(v=>dot(pl.normal,v)<=pl.d+1e-6)),'convex hull planarity');require_(p.vertices.every(v=>p.planes.some(pl=>Math.abs(dot(pl.normal,v)-pl.d)<1e-6)),'hull enclosed vertices');}
 }
 require_(Array.isArray(raw.queries)&&raw.queries.length>0&&raw.queries.length<=512,'query bound');const qids=new Set();
 for(const q of raw.queries){require_(object(q)&&typeof q.id==='string'&&!qids.has(q.id)&&['A','B'].includes(q.actor),'query identity');qids.add(q.id);require_(Number.isInteger(q.mask)&&q.mask>=1&&q.mask<=7,'query mask');
  if(q.kind==='ray')require_(vec(q.from)&&vec(q.to)&&length(sub(q.to,q.from))>EPS,'ray endpoints');
  else if(q.kind==='aim')require_(vec(q.origin)&&finite(q.yaw)&&finite(q.pitch)&&Math.abs(q.pitch)<=1.35&&finite(q.distance)&&q.distance>0,'aim inputs');
  else require_(['sweep','overlap'].includes(q.kind)&&vec(q.feet)&&vec(q.size)&&q.size.every((n:number)=>n>0)&&(q.kind==='overlap'||(vec(q.motion)&&length(q.motion)>EPS)),'shape inputs');
 }
 const s=raw.paired_stream;require_(object(s)&&s.tick_hz===60&&Number.isInteger(s.ticks)&&s.ticks>0&&s.ticks<=10000&&s.mask===1&&finite(s.support_drop_m)&&s.support_drop_m>0&&Array.isArray(s.actors)&&s.actors.length===2,'stream envelope');
 require_(s.actors.every((a:any,i:number)=>object(a)&&a.id===['A','B'][i]&&vec(a.feet)&&vec(a.velocity)),'paired actors');
 return raw as Fixture;
}
type Plane={normal:Vec,d:number};type Poly={id:string,layer:number,vertices:Vec[],planes:Plane[],axes:Vec[]};
function poly(c:Collider):Poly {
 let vertices:Vec[],faces:number[][];
 if(c.shape==='box'){
  const p=c.center!,h=mul(c.size!,.5);vertices=[];
  for(const z of [-1,1])for(const y of [-1,1])for(const x of [-1,1])vertices.push(add(p,[x*h[0],y*h[1],z*h[2]]));
  faces=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]];
 }else {vertices=c.vertices!;faces=c.faces!;}
 const center=mul(vertices.reduce((a,b)=>add(a,b),[0,0,0] as Vec),1/vertices.length);
 const planes:Plane[]=[],satAxes:Vec[]=[...axes];
 const append=(a:Vec)=>{const len=length(a);if(len<EPS)return;const n=mul(a,1/len);if(!satAxes.some(v=>Math.abs(dot(v,n))>1-1e-7))satAxes.push(n);};
 for(const face of faces){const a=vertices[face[0]!]!,b=vertices[face[1]!]!,c_=vertices[face[2]!]!;let n=cross(sub(b,a),sub(c_,a));const norm=length(n);if(norm<EPS)throw new Error('degenerate face');n=mul(n,1/norm);if(dot(n,sub(center,a))>0)n=mul(n,-1);planes.push({normal:n,d:dot(n,a)});append(n);
  for(let i=0;i<face.length;i++){const edge=sub(vertices[face[(i+1)%face.length]!]!,vertices[face[i]!]!);for(const axis of axes)append(cross(axis,edge));}}
 return {id:c.id,layer:c.layer,vertices,planes,axes:satAxes};
}
export function aimDirection(yaw:number,pitch:number):Vec{return [Math.sin(yaw)*Math.cos(pitch),Math.sin(pitch),Math.cos(yaw)*Math.cos(pitch)];}
function rayOne(p:Poly,origin:Vec,motion:Vec){
 if(p.planes.every(v=>dot(v.normal,origin)<v.d+EPS))return null; // Godot hit_from_inside=false.
 let lo=0,hi=1,normal:Vec=[0,0,0];
 for(const plane of p.planes){const distance=plane.d-dot(plane.normal,origin),speed=dot(plane.normal,motion);
  if(Math.abs(speed)<EPS){if(distance<0)return null;continue;}
  const t=distance/speed;if(speed<0){if(t>lo){lo=t;normal=plane.normal;}}else hi=Math.min(hi,t);
  if(lo>hi+EPS)return null;}
 if(lo<0||lo>1||length(normal)<EPS)return null;
 return {hit:true,collider:p.id,fraction:lo,position:add(origin,mul(motion,lo)),normal};
}
function projection(p:Poly,axis:Vec){const values=p.vertices.map(v=>dot(v,axis));return [Math.min(...values),Math.max(...values)];}
function overlapping(p:Poly,center:Vec,half:Vec){return p.axes.every(axis=>{const [lo,hi]=projection(p,axis),radius=dot(axis.map(Math.abs) as Vec,half),value=dot(center,axis);return value+radius>lo!+EPS&&value-radius<hi!-EPS;});}
function sweepOne(p:Poly,center:Vec,half:Vec,motion:Vec){
 if(overlapping(p,center,half))return null; // initial overlap is a separate reject/recovery query.
 let enter=0,exit=1;
 for(const axis of p.axes){const [low,high]=projection(p,axis),r=dot(axis.map(Math.abs) as Vec,half),o=dot(center,axis),v=dot(motion,axis),lo=low!-r,hi=high!+r;
  if(Math.abs(v)<EPS){if(o<lo-EPS||o>hi+EPS)return null;continue;}
  const a=(lo-o)/v,b=(hi-o)/v;enter=Math.max(enter,Math.min(a,b));exit=Math.min(exit,Math.max(a,b));if(enter>exit+EPS)return null;}
 return enter>=0&&enter<1?enter:null;
}
export function buildQueries(f:Fixture){const geometry=f.colliders.filter(c=>!c.visual_only).map(poly);
 return (q:Query):any=>{const candidates=geometry.filter(p=>(p.layer&q.mask)!==0);
  if(q.kind==='ray'||q.kind==='aim'){const origin=q.kind==='aim'?q.origin!:q.from!;const direction=q.kind==='aim'?aimDirection(q.yaw!,q.pitch!):undefined;const motion=direction?mul(direction,q.distance!):sub(q.to!,origin);let best:any={hit:false};
   for(const p of candidates){const h=rayOne(p,origin,motion);if(h&&(!best.hit||h.fraction<best.fraction))best=h;}return direction?{...best,direction}:best;
  }
  const half=mul(q.size!,.5),center=add(q.feet!,[0,half[1],0]);
  if(q.kind==='overlap')return {colliders:candidates.filter(p=>overlapping(p,center,half)).map(p=>p.id).sort()};
  let fraction=1;for(const p of candidates){const t=sweepOne(p,center,half,q.motion!);if(t!==null)fraction=Math.min(fraction,t);}return {fraction};
 };
}
export function execute(f:Fixture){const query=buildQueries(f),queries=f.queries.map(q=>({id:q.id,actor:q.actor,kind:q.kind,result:query(q)}));
 const stream:any[]=[],s=f.paired_stream,actors=s.actors.map(a=>({...a,feet:[...a.feet] as Vec})),size=f.query_contract.actor_size as Vec;const start=performance.now();
 for(let tick=0;tick<s.ticks;tick++)for(const a of actors){const motion=mul(a.velocity,1/s.tick_hz);const movement=query({id:'stream',actor:a.id,kind:'sweep',mask:s.mask,feet:a.feet,size,motion});a.feet=add(a.feet,mul(motion,movement.fraction));const support=query({id:'support',actor:a.id,kind:'ray',mask:s.mask,from:add(a.feet,[0,.1,0]),to:add(a.feet,[0,-s.support_drop_m,0])});stream.push({tick,actor:a.id,feet:[...a.feet],fraction:movement.fraction,support});}
 return {format:1,implementation:'original-typescript-convex-sat-v1',queries,stream,profile:{stream_queries:stream.length*2,stream_query_elapsed_ms:performance.now()-start,scope:'single process wall time; no network, rendering, controller, server capacity or hardware frame-time claim'}};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){const file=process.argv[2],output=process.argv[3];if(!file||!output)throw new Error('usage: node reference.ts fixture.json output.json');const bytes=readFileSync(file);const f=validateFixture(JSON.parse(bytes.toString()));const result={...execute(f),fixture_sha256:createHash('sha256').update(bytes).digest('hex'),source_sha256:createHash('sha256').update(readFileSync(process.argv[1])).digest('hex')};writeFileSync(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({queries:result.queries.length,stream:result.stream.length,output}));}
