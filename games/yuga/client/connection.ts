import { ArenaSimulation } from '../shared/simulation';
import { YUGA_PROTOCOL } from '../shared/types';
import type { ArenaSnapshot, ArenaInput, ArenaCommand, ServerMessage, CommandResult } from '../shared/types';
export interface ArenaConnection { input(input:ArenaInput):void; command(command:ArenaCommand):void; pause(paused:boolean):void; close():void; reconnect?():void }
export interface Callbacks { snapshot(snapshot:ArenaSnapshot):void; welcome(id:string,room:string,online:boolean):void; status(message:string,ready:boolean):void; result(result:CommandResult):void; error(message:string):void }
export function practice(heroId:string,name:string,callbacks:Callbacks):ArenaConnection {
  const sim=new ArenaSimulation({room:'PRACTICE',seed:20261016});
  sim.addPlayer('local-player',name,heroId,'sun');
  let paused=false,closed=false,previous=performance.now(),accumulator=0;
  const advance=()=>{
    const now=performance.now(),elapsed=Math.max(0,Math.min(1,(now-previous)/1000));previous=now;
    if(paused||closed){accumulator=0;return false;}
    accumulator=Math.min(1,accumulator+elapsed);
    // Integer step counts retain fractional time without losing a tick to repeated subtraction.
    const steps=Math.min(20,Math.floor((accumulator+1e-9)/.05));
    accumulator=Math.max(0,accumulator-steps*.05);
    for(let i=0;i<steps;i++)sim.step(.05);
    return steps>0;
  };
  callbacks.welcome('local-player','PRACTICE',false);callbacks.status('Practice · bots on both teams',true);callbacks.snapshot(sim.snapshot());
  const timer=window.setInterval(()=>{advance();if(!paused&&!closed)callbacks.snapshot(sim.snapshot());},50);
  return {
    input:input=>{if(paused||closed)return;const advanced=advance();sim.input('local-player',input);if(advanced)callbacks.snapshot(sim.snapshot());},
    command:command=>{if(closed)return;advance();const result=sim.command('local-player',command);callbacks.result(result);callbacks.snapshot(sim.snapshot());},
    pause:value=>{if(closed||paused===value)return;const advanced=advance();paused=value;accumulator=0;previous=performance.now();if(advanced)callbacks.snapshot(sim.snapshot());},
    close:()=>{closed=true;clearInterval(timer);},
  };
}
export function serverUrl(value:string):string|null {
  if(!value.trim())return null;
  try {const u=new URL(value); if(u.username||u.password||u.search||u.hash)return null;
    if(u.protocol==='https:')u.protocol='wss:';else if(u.protocol==='http:')u.protocol='ws:';
    if(u.protocol!=='wss:'&&!(u.protocol==='ws:'&&['localhost','127.0.0.1','[::1]'].includes(u.hostname)))return null;
    if(u.pathname==='/'||!u.pathname)u.pathname='/ws';return u.toString();
  }catch{return null;}
}
export function defaultServer(){ return ['localhost','127.0.0.1','[::1]'].includes(location.hostname)?`${location.protocol==='https:'?'wss:':'ws:'}//${location.host}/ws`:''; }
export function online(options:{url:string;heroId:string;name:string;room:string},callbacks:Callbacks):ArenaConnection {
  let socket:WebSocket|undefined,closed=false,joined=false,stale=false,lastSnapshot=0,failures=0,retry:number|undefined;
  let room=options.room,token='';
  const identityKey=()=>`yuga.identity.v1:${options.url}:${room}`;
  try{if(room)token=sessionStorage.getItem(identityKey())||'';}catch{/* Session identity remains in memory. */}
  const send=(value:unknown)=>{if(socket?.readyState===WebSocket.OPEN)socket.send(JSON.stringify(value));};
  const connect=()=>{
    if(closed)return;joined=false;stale=false;callbacks.status(failures?'Rejoining your match…':'Connecting to arena…',false);
    try{socket=new WebSocket(options.url);}catch{callbacks.error('Could not open that server. Check its address and try again.');return;}
    const attempt=socket;
    attempt.addEventListener('open',()=>{if(attempt===socket)send({type:'join',protocol:YUGA_PROTOCOL,heroId:options.heroId,name:options.name,...(room?{room}:{}),...(token?{token}:{})});});
    attempt.addEventListener('message',event=>{
      if(attempt!==socket||closed)return;
      let message:ServerMessage;try{message=JSON.parse(String(event.data));}catch{return;}
      if(!message||typeof message!=='object')return;
      if(message.type==='welcome'){
        if(message.protocol!==YUGA_PROTOCOL||message.snapshot?.protocol!==YUGA_PROTOCOL||!Array.isArray(message.snapshot.actors)||!Array.isArray(message.snapshot.neutrals)||!Array.isArray(message.snapshot.goldShards)){closed=true;joined=false;clearInterval(freshness);clearTimeout(retry);callbacks.status('Arena version mismatch',false);callbacks.error('This arena server uses a different game version. Update it to YUGA Confluence.');attempt.close();return;}
        room=message.room;token=message.token;joined=true;stale=false;failures=0;lastSnapshot=Date.now();
        try{sessionStorage.setItem(identityKey(),token);}catch{/* Reconnect still works in this tab. */}
        callbacks.welcome(message.id,room,true);callbacks.status(`Online · ${room}`,true);callbacks.snapshot(message.snapshot);
      }else if(message.type==='snapshot'&&joined){
        if(message.snapshot?.protocol!==YUGA_PROTOCOL||!Array.isArray(message.snapshot.actors)||!Array.isArray(message.snapshot.neutrals)||!Array.isArray(message.snapshot.goldShards))return;
        lastSnapshot=Date.now();if(stale){stale=false;callbacks.status(`Online · ${room}`,true);}callbacks.snapshot(message.snapshot);
      }else if(message.type==='result')callbacks.result(message);
      else if(message.type==='error')callbacks.error(message.message);
    });
    attempt.addEventListener('close',event=>{if(closed||attempt!==socket)return;joined=false;if(event.code===4001){closed=true;clearInterval(freshness);callbacks.status('This match is active in another tab',false);callbacks.error('Your hero was rejoined in another tab. Return to the roster to start a new match.');return;}callbacks.status('Disconnected · your hero is covered by a bot',false);if(++failures<=4)retry=window.setTimeout(connect,Math.min(8000,failures*1500));else callbacks.error('Could not rejoin. Use Reconnect or return to the roster.');});
    attempt.addEventListener('error',()=>{/* close supplies retry and visible recovery. */});
  };
  const freshness=window.setInterval(()=>{if(joined&&!stale&&Date.now()-lastSnapshot>2500){stale=true;callbacks.status('Waiting for server · controls paused',false);}},500);
  connect();
  return {input:input=>{if(joined&&!stale&&!closed)send(input);},command:command=>{if(joined&&!stale&&!closed)send(command);else callbacks.error('Wait for the match connection before taking an action.');},pause:()=>{/* The shared server keeps playing while one client has a menu open. */},close:()=>{closed=true;clearInterval(freshness);clearTimeout(retry);socket?.close();},reconnect:()=>{if(closed)return;clearTimeout(retry);const old=socket;socket=undefined;old?.close();failures=0;connect();}};
}
