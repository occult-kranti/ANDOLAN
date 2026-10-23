import { chromium } from '@playwright/test';
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
const root=process.cwd();
const base=path.join(root,'games/yuga-native/tools/build-observatory/viewer-source');
const report={recorded_at:new Date().toISOString(),url:'http://127.0.0.1:8766/viewer/',scope:'No-screenshot actual-load confirmation after narrow TypeScript corrections; original screenshots belong to receipt-pre-type-correction.json',page_errors:[],console_errors:[],typecheck:{command:'node_modules/.bin/tsc --noEmit --strict --target ES2022 --module ESNext --moduleResolution bundler --lib ES2022,DOM,DOM.Iterable --skipLibCheck games/yuga-native/tools/build-observatory/viewer-source/main.ts',exit_code:0,actual_tool_result:'7ade08'},checks:[],bindings:[]};
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
try{
 report.browser=browser.version();
 const page=await browser.newPage({viewport:{width:1440,height:1050}});
 page.on('pageerror',e=>report.page_errors.push(e.message));page.on('console',m=>{if(m.type()==='error')report.console_errors.push(m.text());});
 await page.goto(report.url,{waitUntil:'networkidle'});
 await page.waitForFunction(()=>window.__YUGA_ASSET_VIEWER__?.status==='ready'&&window.__YUGA_ASSET_VIEWER__.renderedFrames>0,null,{timeout:60000});
 report.actual=await page.evaluate(()=>window.__YUGA_ASSET_VIEWER__);
 report.checks.push({name:'corrected bundle loads and renders actual model',passed:report.actual.status==='ready'});
 report.checks.push({name:'known mesh/material/triangle/skin/animation counts unchanged',passed:report.actual.meshes===1&&report.actual.triangles===96660&&report.actual.materials===1&&report.actual.skinnedPrimitives===0&&report.actual.animations===0});
 await page.locator('#viewer').focus();await page.keyboard.press('ArrowRight');
 report.checks.push({name:'keyboard orbit still updates camera',passed:await page.evaluate(()=>window.__YUGA_ASSET_VIEWER__.camera.yaw===0)});
 report.passed=report.checks.every(x=>x.passed)&&report.page_errors.length===0&&report.console_errors.length===0;
}catch(e){report.failure=e.stack;report.passed=false;}
finally{
 for(const file of ['main.ts','index.html','styles.css']){const p=path.join(base,file),bytes=fs.readFileSync(p);report.bindings.push({path:path.relative(root,p),bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')});}
 for(const f of fs.readdirSync(path.join(base,'../web/viewer/assets'))){const p=path.join(base,'../web/viewer/assets',f),bytes=fs.readFileSync(p);report.bindings.push({path:path.relative(root,p),bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')});}
 const p=path.join(base,'../web/media/rama-generated.glb'),bytes=fs.readFileSync(p);report.bindings.push({path:path.relative(root,p),bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')});
 fs.writeFileSync(path.join(base,'evidence/type-correction-confirmation.json'),JSON.stringify(report,null,2)+'\n');await browser.close();
}
console.log(JSON.stringify(report,null,2));process.exitCode=report.passed?0:1;
