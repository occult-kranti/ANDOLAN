// Drive the archived Vite production entry using only its published DOM and physical controls.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdir,readFile,writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { chromium } from 'playwright';

const {values}=parseArgs({options:{
  url:{type:'string'},archive:{type:'string'},report:{type:'string'},screenshot:{type:'string'},
}});
if(!values.url||!values.archive||!values.report||!values.screenshot) {
  throw Error('Pass --url http://127.0.0.1:PORT/prefix/arena/ --archive package.zip --report check.json --screenshot gameplay.png');
}
const entry=new URL(values.url);
const prefix=new URL('./',entry).pathname;
const html=execFileSync('unzip',['-p',values.archive,'index.html'],{maxBuffer:64*1024*1024});
const response=await fetch(entry);
assert.ok(response.ok&&Buffer.from(await response.arrayBuffer()).equals(html),'server delivers the archived production HTML');
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const viewport={width:1280,height:720};
const evidence={scope:'Sangam Vite production ZIP under a subdirectory, public controls, full-size desktop screenshot',
  archive_sha256:hash(await readFile(values.archive)),html_sha256:hash(html),test_sha256:hash(await readFile(fileURLToPath(import.meta.url))),
  viewport,prefix,checks:[],failed_requests:[],outside_prefix:[],page_errors:[],models:[]};
const assertCheck=(value,description)=>{assert.ok(value,description);evidence.checks.push(description);console.log(description);};
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '/usr/bin/chromium',
  args:['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader','--use-angle=swiftshader']});
const page=await browser.newPage({viewport});
page.setDefaultTimeout(30_000);
const resources=new Set();
page.on('pageerror',e=>evidence.page_errors.push(e.message));
page.on('request',req=>{
  const u=new URL(req.url());
  if(/^https?:$/.test(u.protocol) && (u.origin!==entry.origin || !u.pathname.startsWith(prefix))) evidence.outside_prefix.push(u.pathname);
});
page.on('response',res=>{
  const u=new URL(res.url());
  if(!/^https?:$/.test(u.protocol))return;
  if(res.status()>=400) evidence.failed_requests.push({path:u.pathname,status:res.status()});
  if(res.ok()&&/\.(wasm|glb)$/i.test(u.pathname)) resources.add(u.pathname);
});
async function rendered(mode) {
  await page.waitForFunction(mode=>{
    const hud=document.getElementById('hud'),label=document.getElementById('match-mode');
    return !!hud&&!hud.hidden && !document.querySelector('#loading:not([hidden])') && label?.textContent?.trim().toLowerCase()===mode;
  },mode,{timeout:125_000});
}
async function pressFor(key,predicate) {
  await page.keyboard.down(key);
  try { await predicate(); } finally { await page.keyboard.up(key); }
}
await Promise.all([mkdir(path.dirname(values.report),{recursive:true}),mkdir(path.dirname(values.screenshot),{recursive:true})]);
try {
  evidence.browser=browser.version();
  await page.goto(entry.href,{waitUntil:'domcontentloaded',timeout:120_000});
  await page.locator('#sparring-play').waitFor();
  assertCheck(await page.locator('[data-hero]').count()===14,'public roster exposes fourteen selectable heroes');
  const heroId='sita';
  await page.locator('[data-hero="'+heroId+'"]').click();
  await page.locator('#sparring-play').click();
  await rendered('rust sparring');
  assertCheck((await page.locator('#hero-hudname').innerText()).toLowerCase().includes('sita'),'selected Sita appears on the public sparring HUD');
  const hp = (text)=>Number(text.match(/\d+/)?.[0]);
  const rivalStart=hp(await page.locator('#enemy-score').innerText());
  await pressFor('KeyF',()=>page.waitForFunction(before=>{
    const now=Number(document.querySelector('#enemy-score').textContent.match(/\d+/)?.[0]);
    return Number.isFinite(now)&&now<before;
  },rivalStart,{timeout:35_000}));
  evidence.rival_hp={before:rivalStart,after:hp(await page.locator('#enemy-score').innerText())};
  assertCheck(evidence.rival_hp.after<rivalStart,'ordinary primary fire reduced the rival’s visible HP');
  await page.keyboard.press('KeyQ');
  await page.waitForFunction(()=>/^\d+s$/.test(document.querySelector('#ability-0 .ability-time').textContent));
  evidence.active_ability=await page.locator('#ability-0 .ability-name').innerText();
  await page.screenshot({path:values.screenshot,timeout:120_000});
  evidence.screenshot_sha256=hash(await readFile(values.screenshot));
  assertCheck(!!evidence.active_ability,'the chosen hero’s Q ability activated through the public HUD');
  await page.locator('#sparring-reset').click();
  await rendered('rust sparring');
  await page.waitForFunction(hp=>Number(document.querySelector('#enemy-score').textContent.match(/\d+/)?.[0])===hp && document.querySelector('#ability-0 .ability-time').textContent==='READY',rivalStart);
  assertCheck(true,'reset restores rival health and clears the spent cooldown');
  await page.locator('#sparring-roster').click();await page.locator('#lobby').waitFor();
  await page.locator('[data-hero="ravana"]').click();await page.locator('#sparring-play').click();await rendered('rust sparring');
  assertCheck((await page.locator('#hero-hudname').innerText()).toLowerCase().includes('ravana'),'change hero opens a fresh Ravana session');
  await page.locator('#sparring-roster').click();await page.locator('#practice-play').click();
  await page.waitForFunction(()=>document.querySelector('#hud')&&!document.querySelector('#hud').hidden &&
    !document.querySelector('#loading:not([hidden])') && document.querySelector('#match-mode').textContent.toLowerCase().includes('practice'),undefined,{timeout:150_000});
  await page.keyboard.press('Escape');await page.locator('#leave-game').click();await page.locator('#lobby').waitFor();
  assertCheck(true,'the standard practice path still loads from the shipped menu and exits');
  evidence.models=[...resources].sort();
  assertCheck([...resources].some(p=>/sita[^/]*\.glb/i.test(p)) && [...resources].some(p=>/ravana[^/]*\.glb/i.test(p)),
    'both selected hero GLBs loaded from the package under the deployment prefix');
  assertCheck(!evidence.outside_prefix.length && !evidence.failed_requests.length && !evidence.page_errors.length,
    'the production client stayed inside its deployment directory and completed without asset or runtime errors');
  evidence.passed=true;
} catch(error) {
  evidence.passed=false;evidence.failure=String(error);console.error(error);process.exitCode=1;
  await page.screenshot({path:values.screenshot.replace(/\.png$/,'-failure.png'),timeout:15000}).catch(()=>{});
} finally {
  await writeFile(values.report,JSON.stringify(evidence,null,2)+'\n');await browser.close();
}
