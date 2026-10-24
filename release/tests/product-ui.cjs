'use strict';
// Synthetic workspace only. These checks never log in or call a model provider.
const fs = require('node:fs/promises');
const path = require('node:path');
module.exports = async function ({window, output, consoleErrors, ownerToken}) {
  await fs.mkdir(output, {recursive:true});
  const checks = {};
  let active=window;
  const js = source => active.webContents.executeJavaScript(source);
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
    await fs.writeFile(path.join(output,name+'.png'),(await active.webContents.capturePage()).toPNG());
  };
  try {
    await wait("document.body.innerText.includes('Open your workspace')",'welcome login');
    checks.both_providers_on_welcome=await js("document.body.innerText.includes('Continue with OpenAI')&&document.body.innerText.includes('Continue with Anthropic')");
    await screenshot('login');
    await click('Continue with read-only access');
    await click('Settings');
    await wait("document.body.innerText.includes('Read-only access')",'anonymous account settings');
    checks.anonymous_native_privileges_denied=await js("window.deltaDesktop.settings('saveStorage',{maximum_bytes:21474836480,reserve_bytes:536870912}).then(()=>false,e=>e.message.includes('Sign in'))");
    await click('Sign in to workspace');
    await click('Continue as workspace owner');
    await wait("document.body.innerText.includes('desktop-owner')",'owner login');
    checks.native_login=true;
    await click('Settings');
    await click('Provider account');
    await wait("document.body.innerText.includes('Sign in with ChatGPT')",'provider login before a plan');
    checks.provider_controls_before_plan=await js("document.body.innerText.includes('Sign in with your Claude account')");
    await screenshot('provider-login');
    await click('Appearance');
    await js("(()=>{const s=document.querySelector('.settings-content select');s.value='reduced';s.dispatchEvent(new Event('change',{bubbles:true}));})()");
    await wait("document.documentElement.dataset.motion==='reduced'",'saved motion preference');
    await click('Workspace access');
    await click('Sign out of workspace');
    await wait("document.body.innerText.includes('Open your workspace')",'workspace logout');
    checks.workspace_signout=true;
    await click('Continue as workspace owner');
    await wait("document.body.innerText.includes('desktop-owner')",'owner login after logout');
    checks.preference_survives_login=await js("document.documentElement.dataset.motion==='reduced'");
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
    await click('Settings');
    await click('Storage');
    await wait("document.body.innerText.includes('GiB used')",'desktop workspace status');
    await click('Save storage limits');
    await wait("document.querySelector('.operation-result')?.innerText.includes('maximum_bytes')",'saved storage limits');
    checks.native_settings_bridge=true;
    await screenshot('settings');
    window.setSize(760,900);
    await screenshot('settings-narrow');
    checks.settings_scroll=await js("(()=>{const e=document.querySelector('.settings-content');e.scrollTop=e.scrollHeight;return e.scrollHeight<=e.clientHeight||e.scrollTop>0;})()");
    await screenshot('settings-narrow-bottom');
    const {BrowserWindow}=require('electron');
    const browser=new BrowserWindow({width:1000,height:850,show:true,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,partition:'login-browser-check'}});
    active=browser;
    browser.webContents.on('console-message',details=>{if(details.level==='error'&&!details.message.includes('401'))consoleErrors.push(details.message);});
    try {
      await browser.loadURL(window.webContents.getURL());
      await click('Sign in');
      await wait("document.querySelector('#token')",'browser token form');
      await screenshot('browser-login');
      const setToken=async token=>js(`(()=>{const input=document.querySelector('#token');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,${JSON.stringify(token)});input.dispatchEvent(new Event('input',{bubbles:true}));})()`);
      const submit=async()=>{await wait("!document.querySelector('.signin button[type=submit]').disabled",'token form ready');await js("document.querySelector('.signin button[type=submit]').click()");};
      await setToken('invalid-fixture-token');
      await submit();
      await wait("document.querySelector('.signin [role=alert]')?.innerText.includes('does not accept')",'invalid token feedback');
      checks.invalid_browser_token=true;
      await setToken(ownerToken);
      await submit();
      await wait("document.body.innerText.includes('desktop-owner')&&!document.querySelector('.signin')",'browser owner login');
      checks.browser_session_only_token=await js("Boolean(sessionStorage.getItem('delta.token'))&&!localStorage.getItem('delta.token')");
      await click('Settings');
      await click('Sign out of workspace');
      await wait("document.body.innerText.includes('Sign in')",'browser signout');
      checks.browser_signout=await js("!sessionStorage.getItem('delta.token')&&!localStorage.getItem('delta.token')");
      await click('Sign in');
      await setToken(ownerToken);
      await js("document.querySelector('.signin input[type=checkbox]').click()");
      await submit();
      await wait("document.body.innerText.includes('desktop-owner')&&!document.querySelector('.signin')",'remembered browser login');
      checks.remember_browser_token=await js("Boolean(localStorage.getItem('delta.token'))&&!sessionStorage.getItem('delta.token')");
      await click('Settings');
      await click('Appearance');
      await screenshot('browser-settings');
      checks.browser_settings=true;
    } finally {browser.destroy();active=window;}
    checks.no_console_errors=consoleErrors.length===0;
    if(Object.values(checks).some(value=>!value))throw new Error('A desktop check failed.');
    await fs.writeFile(path.join(output,'product-ui.json'),JSON.stringify({status:'passed',checks,consoleErrors},null,2)+'\n');
  } catch(error) {
    await screenshot('failure');
    await fs.writeFile(path.join(output,'product-ui.json'),JSON.stringify({status:'failed',checks,consoleErrors,error:error.message,body:await js('document.body.innerText')},null,2)+'\n');
    throw error;
  }
};
