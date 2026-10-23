from pathlib import Path
import datetime, hashlib, importlib.util,json,os,subprocess,threading
repo=Path('/workspace/ANDOLAN');source=repo/'games/yuga-native/tools/build-observatory/observatory.py'
base=Path('/workspace/scratch/production-stage-oct23/review');run=base/'browser-integration';run.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('obs_review',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
state=m.state_directory(repo,run/'state')
if not (state/'state.json').exists():m.update_state(state,initialize=('browser-review','Independent browser integration — synthetic review jobs'))
m.update_state(state,{'id':'active-review','title':'Actual integration review','owner':'independent reviewer','stage':'Browser/backend integration','status':'running','device':'CPU','pid':os.getpid(),'summary':'Synthetic test record for this real running verification process, not game work.','next_step':'Record exact independent checks'})
m.update_state(state,{'id':'queued-fixture','title':'Queued fixture','status':'queued','device':'CPU','summary':'Only a synthetic review input'})
observer=m.Observatory(repo,state);server=m.make_server(observer,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
script=run/'exercise.mjs'
script.write_text('''import { chromium } from '/workspace/ANDOLAN/node_modules/playwright/index.mjs';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--disable-gpu']});
const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];const checks=[];
page.on('pageerror',e=>errors.push(e.message));
const check=(name,passed,detail=null)=>checks.push({name,passed,detail});
try {
await page.goto(process.argv[2],{waitUntil:'networkidle'});
await page.locator('#connection-label').filter({hasText:'Live worker observation'}).waitFor();
check('actual_backend_live_label',await page.locator('#connection-label').textContent()==='Live worker observation');
check('actual_qualified_job_running',(await page.locator('#queue-summary').textContent()).includes('1 running'));
await page.selectOption('#status-filter','queued');
check('filtered_selection_is_visible',(await page.locator('#inspector-title').textContent())==='Queued fixture');
await page.selectOption('#status-filter','complete');
check('empty_filter_has_empty_inspector',await page.locator('#empty-queue').isVisible()&&(await page.locator('#inspector-title').textContent())==='No job selected');
await page.getByRole('button',{name:'Clear filters',exact:true}).click();
await page.getByRole('button',{name:'Pause updates',exact:true}).click();
check('pause_marks_recorded_running',(await page.locator('#job-list').textContent()).includes('Recorded running')&&(await page.locator('#pause-button').getAttribute('aria-pressed'))==='true');
await page.getByRole('button',{name:'Refresh now',exact:true}).click();await page.waitForTimeout(100);
check('manual_refresh_keeps_pause',(await page.locator('#pause-button').getAttribute('aria-pressed'))==='true');
await page.getByRole('button',{name:'Resume updates',exact:true}).click();
await page.waitForFunction(()=>document.querySelector('#connection-label').textContent==='Live worker observation');
check('resume_restores_live',(await page.locator('#queue-summary').textContent()).includes('1 running'));
await page.evaluate(()=>document.fonts.ready);check('font_usable',await page.evaluate(()=>document.fonts.check('16px "Noto Sans"')));
check('gpu_not_invented',(await page.locator('#gpu-observation').textContent()).includes('No attached GPU observed'));
check('no_page_errors',errors.length===0,errors);
console.log(JSON.stringify({checks,all_pass:checks.every(c=>c.passed),javascript_errors:errors,browser:browser.version()}));
}finally{await browser.close();}
''')
try:
 r=subprocess.run(['node',str(script),f'http://127.0.0.1:{server.server_port}/'],capture_output=True,text=True,timeout=30,cwd=repo)
 body=json.loads(r.stdout) if r.returncode==0 else {'all_pass':False,'stdout':r.stdout,'stderr':r.stderr}
 body.update({'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Actual current Python backend plus current frontend in Chromium using reviewer-owned state. Jobs explicitly synthetic; no actual game/model/GPU work. No extra screenshot/polish pass.','exit_code':r.returncode,'source_hashes':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,source.parent/'web/index.html',source.parent/'web/app.js',source.parent/'web/styles.css']}})
finally:server.shutdown();server.server_close();thread.join(timeout=3)
body['owned_server_stopped']=True;(run/'receipt.json').write_text(json.dumps(body,indent=2)+'\n');print(json.dumps(body,indent=2))
