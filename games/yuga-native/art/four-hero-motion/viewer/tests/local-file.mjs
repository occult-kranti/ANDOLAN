import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile,writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath,pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { chromium } from 'playwright';

const {values} = parseArgs({options:{root:{type:'string',default:fileURLToPath(new URL('../..',import.meta.url))},report:{type:'string'}}});
const root=resolve(values.root);
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox','--disable-dev-shm-usage']});
try {
    const page=await browser.newPage({viewport:{width:780,height:650},reducedMotion:'reduce'});
    page.setDefaultTimeout(90000);
    const outside=[],errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.route(/^https?:/,r=>{outside.push(r.request().url());return r.abort();});
    const href=pathToFileURL(resolve(root,'viewer/index.html'));
    href.search='hero=krishna&clip=cast3&view=rear';
    await page.goto(href.href,{waitUntil:'load'});
    await page.locator('#model-file').waitFor({state:'visible'});
    const pick=id=>page.locator('#model-file').setInputFiles(resolve(root,'models',id+'.glb'));
    await pick('shiva');
    await page.waitForFunction(()=>document.getElementById('message').textContent.includes('uses krishna.glb'));
    assert.equal(await page.locator('#play').isDisabled(),true);
    const ready=id=>page.waitForFunction(h=>window.yugaRigInfo?.().ready && window.yugaRigInfo().hero===h,id,{timeout:120000});
    await pick('krishna');await ready('krishna');
    const info=()=>page.evaluate(()=>window.yugaRigInfo());
    assert.equal((await info()).clip,'cast3');assert.equal((await info()).yaw,180);
    await page.locator('#play').click();await page.waitForFunction(()=>window.yugaRigInfo().time>.06);
    await page.locator('#play').click();assert.equal((await info()).playing,false);
    async function seek(n){
        const frames=(await info()).rendered;
        await page.locator('#scrub').evaluate((el,p)=>{el.value=String(Number(el.max)*p);el.dispatchEvent(new Event('input'));},n);
        await page.waitForFunction(previous=>window.yugaRigInfo().rendered>previous,frames);
        return (await info()).pose;
    }
    const a=await seek(.15),b=await seek(.68);
    const max=Math.max(...[0,4,8].map(n=>{
        const x=a.slice(n,n+4),y=b.slice(n,n+4);
        return 2*Math.acos(Math.min(1,Math.abs(x.reduce((v,c,i)=>v+c*y[i],0)/(Math.hypot(...x)*Math.hypot(...y)))))*180/Math.PI;
    }));
    assert(max>.01);
    await page.locator('#hero').selectOption('shiva');
    await page.locator('#model-file').waitFor({state:'visible'});assert.equal((await info()).ready,false);
    await pick('shiva');await ready('shiva');assert.equal((await info()).jointCount,163);
    await page.locator('#hero').selectOption('krishna');await ready('krishna');
    assert.equal(await page.locator('#model-file').isVisible(),false);
    assert.deepEqual(outside,[]);assert.deepEqual(errors,[]);
    const modelSha256=Object.fromEntries(await Promise.all(['krishna','shiva'].map(async id=>[
        id,createHash('sha256').update(await readFile(resolve(root,'models',id+'.glb'))).digest('hex')
    ])));
    const report={browser:await browser.version(),openMode:'file:// with standard Chromium file permissions and a native File input',modelSha256,
        runtimeSha256:createHash('sha256').update(await readFile(resolve(root,'viewer/app.min.js'))).digest('hex'),
        arbitraryNetworkRequests:outside.length,uncaughtBrowserErrors:errors.length,krishnaMaxSampledJointRotationDegrees:Number(max.toFixed(6)),
        checks:['Mismatched GLB leaves the picker visible','Krishna loads from a user-selected local blob','Deep link selects cast3 and the rear camera',
            'Playback advances and pauses','Two seek positions produce distinct live joint rotations','New hero requests its matching GLB','Already selected hero reopens without another prompt']};
    if(values.report) await writeFile(values.report,JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify(report));
} finally {await browser.close();}
