import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { createReadStream, existsSync } from 'node:fs';
import { readFile, writeFile, stat, mkdir } from 'node:fs/promises';
import { resolve, extname, sep, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
const here = fileURLToPath(new URL('../..', import.meta.url));
const {values} = parseArgs({options:{root:{type:'string',default:here}, report:{type:'string'}, screenshots:{type:'string'}}});
const root = resolve(values.root);
const server = createServer(async (req,res) => {
    try {
        const path = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
        if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405).end(); return; }
        const file = resolve(root, '.' + path + (path.endsWith('/') ? 'index.html' : ''));
        if (!file.startsWith(root+sep) || !(await stat(file)).isFile()) throw Error('Missing');
        const types = {'.html':'text/html','.js':'text/javascript','.css':'text/css','.glb':'model/gltf-binary','.woff2':'font/woff2'};
        res.setHeader('Content-Type',types[extname(file)] || 'application/octet-stream');
        if (req.method === 'HEAD') res.end(); else createReadStream(file).pipe(res);
    } catch { res.writeHead(404).end(); }
});
await new Promise((ok,fail)=>server.once('error',fail).listen(0,'127.0.0.1',ok));
const base = 'http://127.0.0.1:'+server.address().port;
let browser;
try {
    browser = await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || (existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),
        args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox','--disable-dev-shm-usage']});
    const page = await browser.newPage({viewport:{width:1000,height:740},reducedMotion:'reduce'});
    page.setDefaultTimeout(90000);
    const errors=[], external=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',route=>{
        const u=new URL(route.request().url());
        if (u.protocol.startsWith('http') && u.origin!==base){external.push(u.href);return route.abort();}
        return route.continue();
    });
    const info=()=>page.evaluate(()=>window.yugaRigInfo());
    const ready=id=>page.waitForFunction(h=>window.yugaRigInfo?.().ready && window.yugaRigInfo().hero===h,id,{timeout:150000});
    const digest = bytes => createHash('sha256').update(bytes).digest('hex');
    const output={browser:await browser.version(),renderer:'Chromium WebGL2 / ANGLE SwiftShader',runtimeSha256:digest(await readFile(resolve(root,'viewer/app.min.js'))),heroes:{},checks:[]};
    await page.goto(base+'/viewer/?hero=rama&clip=volley_release&view=side',{waitUntil:'domcontentloaded'});
    await ready('rama'); assert.equal((await info()).clip,'volley_release'); assert.equal((await info()).yaw,90);
    output.checks.push('Rama deep link selected volley_release and the side camera');
    for (const hero of ['rama','hanuman','shiva','krishna']) {
        if (hero!=='rama') {await page.locator('#hero').selectOption(hero);await ready(hero);}
        const buf=await readFile(resolve(root,'models',hero+'.glb'));
        const gltf=JSON.parse(buf.subarray(20,20+buf.readUInt32LE(12)).toString('utf8'));
        const expected=gltf.animations.map(a=>a.name).sort();
        const found=await page.locator('[data-clip]').evaluateAll(bs=>bs.map(b=>b.dataset.clip).sort());
        assert.deepEqual(found,expected);
        for (const name of found) {
            await page.locator('[data-clip="'+name+'"]').evaluate(b=>b.click());
            assert.equal((await info()).clip,name);
        }
        for (const [view,angle] of Object.entries({front:0,side:90,rear:180})) {
            await page.locator('[data-view="'+view+'"]').click();assert.equal((await info()).yaw,angle);
        }
        await page.locator('[data-view="front"]').click();
        await page.locator('[data-clip="cast3"]').click();
        async function seek(fraction) {
            const before=(await info()).rendered;
            await page.locator('#scrub').evaluate((slider,v)=>{ slider.value=String(Number(slider.max)*v);slider.dispatchEvent(new Event('input',{bubbles:true})); },fraction);
            await page.waitForFunction(n=>window.yugaRigInfo().rendered>n,before);
            return info();
        }
        const a=await seek(.08),b=await seek(.66);
        assert.equal(a.pose.length,12);assert.equal(b.pose.length,12);
        const angles = [0,4,8].map(start=>{
            const q1=a.pose.slice(start,start+4), q2=b.pose.slice(start,start+4);
            const dot=q1.reduce((sum,x,i)=>sum+x*q2[i],0)/(Math.hypot(...q1)*Math.hypot(...q2));
            return 2*Math.acos(Math.min(1,Math.abs(dot)))*180/Math.PI;
        });
        const delta=Math.max(...angles);
        assert(delta>.01,hero+' actual joints stayed still across seek');
        assert(b.meshCount>0 && b.jointCount>=100 && !b.playing);
        output.heroes[hero]={clips:expected.length,joints:b.jointCount,skinnedSurfaces:b.meshCount,maxSampledJointRotationDegrees:Number(delta.toFixed(6)),assetSha256:digest(buf)};
        console.log(hero,output.heroes[hero]);
        if (values.screenshots) {
            await mkdir(values.screenshots,{recursive:true});
            await page.screenshot({path:resolve(values.screenshots,hero+'.png')});
        }
    }
    await page.locator('#scene').focus(); const front=await info();
    await page.keyboard.press('ArrowRight');await page.keyboard.press('ArrowUp');await page.keyboard.press('+');
    const orbit=await info();assert(orbit.yaw!==front.yaw && orbit.pitch>front.pitch && orbit.zoom<front.zoom);
    const box=await page.locator('#scene').boundingBox();await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);
    await page.mouse.down();await page.mouse.move(box.x+box.width*.5+45,box.y+box.height*.5+20,{steps:3});await page.mouse.up();
    assert((await info()).yaw!==orbit.yaw);
    await page.locator('#speed').selectOption('2');await page.locator('#loop').uncheck();
    await page.locator('#play').click();await page.waitForFunction(()=>{const i=window.yugaRigInfo();return !i.playing && i.time===i.duration;});
    await page.locator('#scene').focus();await page.keyboard.press('Space');await page.waitForFunction(()=>window.yugaRigInfo().playing);
    await page.keyboard.press('Space');const frozen=(await info()).time;
    await page.waitForTimeout(200);assert.equal((await info()).time,frozen);
    await page.locator('#hero').evaluate(picker=>{ for(const id of ['shiva','rama','hanuman']){picker.value=id;picker.dispatchEvent(new Event('change',{bubbles:true}));} });
    await ready('hanuman');assert.equal(await page.locator('#title').innerText(),'Hanuman');
    await page.setViewportSize({width:375,height:750});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
    output.checks.push('Every embedded clip selected on each hero', 'All three camera presets on each model',
        'Four per-hero, before/after nonzero live skinned-bone rotation checks', 'Pointer and keyboard orbit and keyboard zoom',
        'Scrub, speed, non-looping end, replay and pause', 'Rapid hero selection shows the final requested character','No horizontal overflow at 375 pixels','No external runtime requests or browser errors');
    if (values.report) {await mkdir(dirname(resolve(values.report)),{recursive:true});await writeFile(values.report,JSON.stringify(output,null,2)+'\n');}
} finally {await browser?.close();await new Promise(ok=>server.close(ok));}
