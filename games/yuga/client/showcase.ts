import * as pc from 'playcanvas';
import { HeroModelLibrary, type HeroModel } from './hero-models';
import { createOriginalEnvironment } from './environment-light';

export interface HeroShowcase {
  setHero(id:string):Promise<void>;
  setClip(clip:string):void;
  diagnostics():unknown;
  destroy():void;
}

/** A real skinned-asset viewer. It uses the same model files and animation tracks as the arena. */
export function createHeroShowcase(canvas:HTMLCanvasElement):HeroShowcase {
  const app=new pc.Application(canvas,{graphicsDeviceOptions:{alpha:false,antialias:true,powerPreference:'high-performance'}});
  app.setCanvasFillMode(pc.FILLMODE_NONE);app.setCanvasResolution(pc.RESOLUTION_AUTO);app.graphicsDevice.maxPixelRatio=Math.min(devicePixelRatio,1.25);
  app.scene.ambientLight=new pc.Color(.47,.52,.57);app.scene.exposure=1.1;
  const environment=createOriginalEnvironment(app);
  const camera=new pc.Entity('hero portrait camera');camera.addComponent('camera',{fov:36,nearClip:.1,farClip:30,clearColor:new pc.Color(.045,.09,.115)});app.root.addChild(camera);camera.setPosition(0,1.25,4.5);camera.lookAt(0,1.05,0);
  const key=new pc.Entity('warm studio key');key.addComponent('light',{type:'directional',color:new pc.Color(1,.86,.68),intensity:2,castShadows:true,shadowResolution:1024,shadowDistance:12,normalOffsetBias:.03});key.setEulerAngles(43,35,0);app.root.addChild(key);
  const fill=new pc.Entity('cool studio fill');fill.addComponent('light',{type:'directional',color:new pc.Color(.65,.8,1),intensity:.7});fill.setEulerAngles(30,-135,0);app.root.addChild(fill);
  const floor=new pc.Entity('studio floor');floor.addComponent('render',{type:'cylinder'});floor.setLocalScale(3,.07,3);floor.setPosition(0,-.04,0);app.root.addChild(floor);
  const material=new pc.StandardMaterial();material.diffuse.set(.055,.105,.125);material.gloss=.25;material.update();floor.render!.material=material;
  const library=new HeroModelLibrary(app),holder=new pc.Entity('hero turntable');app.root.addChild(holder);holder.setEulerAngles(0,-18,0);
  let current:HeroModel|null=null,disposed=false,cleaned=false,request=0,clip='idle';
  const pending=new Set<Promise<void>>();
  const controller=new AbortController();
  const visibility=()=>{const active=!disposed&&!document.hidden;app.autoRender=active;app.renderNextFrame=active;library.setActive(active);};
  document.addEventListener('visibilitychange',visibility,{signal:controller.signal});
  let dragging=false,last=0,angle=-18;
  canvas.addEventListener('pointerdown',e=>{dragging=true;last=e.clientX;canvas.setPointerCapture(e.pointerId);},{signal:controller.signal});
  canvas.addEventListener('pointermove',e=>{if(!dragging)return;angle+=(e.clientX-last)*.45;last=e.clientX;holder.setEulerAngles(0,angle,0);},{signal:controller.signal});
  for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,()=>dragging=false,{signal:controller.signal});
  canvas.addEventListener('keydown',e=>{if(e.code==='ArrowLeft'||e.code==='ArrowRight'){e.preventDefault();angle+=e.code==='ArrowLeft'?-12:12;holder.setEulerAngles(0,angle,0);}},{signal:controller.signal});
  const resize=()=>{const r=canvas.getBoundingClientRect();if(r.width&&r.height)app.resizeCanvas(r.width,r.height);};const observer=new ResizeObserver(resize);observer.observe(canvas);resize();app.start();visibility();
  const setClip=(next:string)=>{clip=next;const anim=current?.root.anim;if(!anim)return;const action=anim.findAnimationLayer('Action');if(action)action.weight=0;anim.baseLayer!.transition(next,.15);};
  const cleanup=()=>{if(cleaned)return;cleaned=true;library.destroy();holder.destroy();floor.destroy();material.destroy();environment.destroy();app.destroy();};
  return {
    setHero(id){if(disposed)return Promise.reject(new Error('Hero viewer is closed.'));const serial=++request;current?.destroy();current=null;const loading=library.preload([id]).then(()=>{if(disposed||serial!==request)return;current=library.instantiate(id,`showcase-${id}-${serial}`,holder);if(!current)throw new Error('The selected hero model could not be created.');setClip('idle');});pending.add(loading);void loading.then(()=>pending.delete(loading),()=>pending.delete(loading));return loading;},
    setClip,
    diagnostics:()=>({clip,hero:current?.diagnostic(),library:library.diagnostics()}),
    destroy(){if(disposed)return;disposed=true;controller.abort();observer.disconnect();app.autoRender=false;app.renderNextFrame=false;library.setActive(false);void Promise.allSettled([...pending]).then(cleanup);},
  };
}
