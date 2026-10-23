import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import {writeFileSync} from 'node:fs';
const require=createRequire('/workspace/ANDOLAN/package.json');
const {chromium}=require('@playwright/test');
const output='/workspace/scratch/ten-rounds-oct23/root/';
const base='http://127.0.0.1:8770';
const server=spawn('python3',['-m','http.server','8770','--bind','127.0.0.1','--directory','/workspace/ANDOLAN/games/yuga-native/tools/build-observatory/web'],{stdio:'ignore'});
const checks=[],errors=[];
let browser;
function check(name,passed,detail=null){checks.push({name,passed,detail});if(!passed)throw Error(name);}
try{
  for(let n=0;n<30;n++){try{if((await fetch(base+'/status.json')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
  browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(base,{waitUntil:'networkidle'});
  await page.waitForSelector('.job-row');
  check('saved snapshot label',await page.locator('#connection-label').innerText()==='Saved snapshot — not live');
  check('twelve explicit jobs',await page.locator('.job-row').count()===12);
  for(const node of await page.locator('.artifact-image').all()){await node.scrollIntoViewIfNeeded();await node.evaluate(img=>img.decode());}
  check('all five actual artifact previews load',await page.locator('.artifact-image').evaluateAll(xs=>xs.length===5&&xs.every(x=>x.naturalWidth>0)));
  check('desktop has no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.getByRole('button',{name:/Animated|Temporal|temporal|effects/i}).first().click();
  const clip=page.getByRole('link',{name:'Watch actual effects study (6 seconds)'});
  check('effects job has actual clip link',(await clip.getAttribute('href')).endsWith('/media/reused-effects.mp4'));
  await page.screenshot({path:output+'dashboard-published-desktop.png',fullPage:true});
  const media=await browser.newPage();
  await media.goto(base+'/media/reused-effects.mp4',{waitUntil:'domcontentloaded'});
  await media.waitForFunction(()=>{const v=document.querySelector('video');return v&&v.readyState>=2;},{timeout:15000});
  const facts=await media.locator('video').evaluate(v=>({width:v.videoWidth,height:v.videoHeight,duration:v.duration,error:v.error?.code??null}));
  check('actual Chromium decodes 960x640 six-second MP4',facts.width===960&&facts.height===640&&Math.abs(facts.duration-6)<.01&&facts.error===null,facts);
  await media.locator('video').evaluate(async v=>{v.muted=true;v.currentTime=0;await v.play();});
  await media.waitForFunction(()=>document.querySelector('video').currentTime>.2);
  check('actual clip playback advances',await media.locator('video').evaluate(v=>v.currentTime>.2));
  await media.screenshot({path:output+'effects-published-playback.png'});
  await page.setViewportSize({width:390,height:844});
  await page.goto(base,{waitUntil:'networkidle'});
  check('mobile has no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  check('mobile retains snapshot and all ten stages',(await page.locator('#connection-label').innerText()).includes('not live')&&await page.locator('.milestone').count()===10);
  await page.screenshot({path:output+'dashboard-published-mobile.png',fullPage:true});
  check('no unhandled page errors',errors.length===0,errors);
}catch(e){errors.push(String(e));process.exitCode=1;}
finally{if(browser)await browser.close();server.kill('SIGTERM');writeFileSync(output+'browser-published-snapshot.json',JSON.stringify({passed:checks.every(x=>x.passed)&&errors.length===0,checks,errors,scope:'Actual local static-snapshot dashboard and Chromium video playback. No game-quality or network-play acceptance.'},null,2)+'\n');}
