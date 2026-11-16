const fs = require('fs');
const { chromium } = require('/workspaces/ANDOLAN/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({headless:true,args:['--no-sandbox']});
  const page = await browser.newPage({viewport:{width:1440,height:1080},timezoneId:"America/New_York"});
  const report = {scope:'Local static dashboard layout and interaction; no public deployment, native input or gameplay claim',checks:[],page_errors:[]};
  page.on('pageerror', error=>report.page_errors.push(String(error)));
  const check = (name,passed)=>{report.checks.push({name,passed});if(!passed)throw Error(name)};
  try {
    await page.goto('http://127.0.0.1:8779/',{waitUntil:'networkidle'});
    check('saved snapshot label',(await page.locator('#connection-label').innerText())==='Saved snapshot — not live');
    check('active Sanctum title',(await page.locator('#run-title').innerText())==='YUGA · Sanctum — local 5v5 Casual');
    check('six jobs',await page.locator('.job-row').count()===6);
    check('six artifacts',await page.locator('#artifact-list .artifact').count()===6);
    check('eight tactical gates',await page.locator('.milestone').count()===8);
    check('three review stages',await page.locator('.milestone [data-status=review]').count()===3);
    check('two gated stages',await page.locator('.milestone [data-status=blocked]').count()===2);
    await page.locator('#status-filter').selectOption('queued');
    check('queued delivery filter',await page.locator('.job-row').count()===1 && await page.locator('.job-row').getAttribute('data-job-id')==='sanctum-delivery');
    await page.locator('#clear-filters').click();
    await page.locator('[data-job-id="sanctum-source"]').focus();
    await page.keyboard.press('Enter');
    check('keyboard inspector selection',(await page.locator('#inspector-title').innerText())==='Sanctum local Casual source prototype');
    await page.locator('#pause-button').click();
    check('pause state',await page.locator('#pause-button').getAttribute('aria-pressed')==='true');
    await page.locator('#refresh-button').click();
    await page.waitForTimeout(500);
    check('refresh preserves pause',await page.locator('#pause-button').getAttribute('aria-pressed')==='true');
    await page.locator('#pause-button').click();
    for (const img of await page.locator('#lead-image, #artifact-list img').all()) {
      await img.scrollIntoViewIfNeeded();
      check('artifact image decoded '+await img.getAttribute('src'), await img.evaluate(async x=>{await x.decode();return x.complete&&x.naturalWidth>0}));
    }
    await page.evaluate(()=>window.scrollTo(0,0));
    check('desktop no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:'/tmp/yuga-dashboard-sanctum-r2/desktop.png',fullPage:true});
    await page.setViewportSize({width:390,height:844});
    await page.evaluate(()=>window.scrollTo(0,0));
    check('mobile no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:'/tmp/yuga-dashboard-sanctum-r2/mobile.png',fullPage:true});
    check('no page errors',report.page_errors.length===0);
    report.passed=true;
  } catch (error) { report.passed=false; report.failure=String(error); process.exitCode=1; }
  finally { fs.writeFileSync('/tmp/yuga-dashboard-sanctum-r2/browser-check.json',JSON.stringify(report,null,2)+'\n'); await browser.close(); }
  console.log(JSON.stringify({passed:report.passed,checks:report.checks.length,failure:report.failure}));
})();
