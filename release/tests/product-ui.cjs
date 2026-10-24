'use strict';
// Synthetic workspace only. These checks never log in or call a model provider.
const fs = require('node:fs/promises');
const path = require('node:path');
module.exports = async function ({window, output, consoleErrors}) {
  await fs.mkdir(output, {recursive:true});
  const checks = {};
  const js = source => window.webContents.executeJavaScript(source);
  const wait = async (source, label, milliseconds=30000) => {
    const until=Date.now()+milliseconds;
    while(Date.now()<until) {
      if(await js(`Boolean(${source})`)) return;
      await new Promise(resolve=>setTimeout(resolve,200));
    }
    throw new Error('Desktop check timed out: '+label);
  };
  const click = async label => {
    await wait(`Array.from(document.querySelectorAll('button')).some(b=>b.textContent.trim()===${JSON.stringify(label)}&&!b.disabled)`,label);
    await js(`Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()===${JSON.stringify(label)}).click()`);
  };
  const screenshot = async name => {
    await new Promise(resolve=>setTimeout(resolve,300));
    await fs.writeFile(path.join(output,name+'.png'),(await window.webContents.capturePage()).toPNG());
  };
  try {
    await click('New TESS investigation');
    await wait("document.querySelector('.observation-choice input[type=checkbox]')",'indexed observation');
    await js("document.querySelector('.observation-choice input[type=checkbox]').click()");
    await click('Save investigation');
    await click('Approve this exact plan');
    await click('Run approved plan');
    await wait("document.querySelector('.evidence-column')?.innerText.includes('1 complete')",'completed analysis',60000);
    await click('Inspect plots');
    await wait("document.querySelectorAll('.product-plot canvas').length>=3",'three evidence plots');
    checks.manual_plan_approval_execution_and_plots=true;
    checks.sandbox=window.webContents.getLastWebPreferences().sandbox===true;
    checks.fonts=await js(`document.fonts.ready.then(()=>document.fonts.check('400 12px "IBM Plex Sans"'))`);
    await screenshot('investigation');
    await click('All operations');
    await wait("document.querySelector('select')?.options.length>20",'operation catalog');
    await js(`(()=>{const s=document.querySelector('select');s.value='get /api/methods';s.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    await click('Read result');
    await wait("document.querySelector('.operation-result')?.innerText.includes('tess-bls')",'method response');
    checks.generated_operation_form=true;
    await screenshot('operations');
    await click('Return');
    await wait("document.body.innerText.includes('State: ready.')",'saved investigation after navigation');
    checks.saved_investigation_navigation=true;
    await click('Workspace');
    await wait("document.body.innerText.includes('GiB used')",'desktop workspace status');
    await click('Save storage limits');
    await wait("document.querySelector('.operation-result')?.innerText.includes('maximum_bytes')",'saved storage limits');
    checks.native_settings_bridge=true;
    await screenshot('settings');
    window.setSize(760,900);
    await screenshot('settings-narrow');
    checks.settings_scroll=await js("(()=>{const e=document.querySelector('.operations-layout');e.scrollTop=e.scrollHeight;return e.scrollHeight<=e.clientHeight||e.scrollTop>0;})()");
    await screenshot('settings-narrow-bottom');
    checks.no_console_errors=consoleErrors.length===0;
    if(Object.values(checks).some(value=>!value))throw new Error('A desktop check failed.');
    await fs.writeFile(path.join(output,'product-ui.json'),JSON.stringify({status:'passed',checks,consoleErrors},null,2)+'\n');
  } catch(error) {
    await screenshot('failure');
    await fs.writeFile(path.join(output,'product-ui.json'),JSON.stringify({status:'failed',checks,consoleErrors,error:error.message,body:await js('document.body.innerText')},null,2)+'\n');
    throw error;
  }
};
