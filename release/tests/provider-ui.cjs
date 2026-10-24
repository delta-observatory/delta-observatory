'use strict';
// Isolated renderer fixture. No provider, account, browser, or workspace connection.
const {app,BrowserWindow}=require('electron');
const fs=require('node:fs/promises'),path=require('node:path');
if(process.env.DELTA_UI_VIRTUAL_DISPLAY!=='1')throw new Error('Run this check through the isolated display script.');
app.disableHardwareAcceleration();app.enableSandbox();
app.setPath('userData',process.env.DELTA_PROVIDER_UI_PROFILE);
app.whenReady().then(async()=>{
 const out=process.env.DELTA_PROVIDER_UI_OUTPUT;await fs.mkdir(out,{recursive:true});
 const window=new BrowserWindow({width:1100,height:1000,show:true,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false}});
 const errors=[],checks={};window.webContents.on('console-message',d=>{if(d.level==='error')errors.push(d.message);});
 const js=s=>window.webContents.executeJavaScript(s);
 const wait=async s=>{for(let n=0;n<100;n++){if(await js(s))return;await new Promise(r=>setTimeout(r,50));}throw new Error('Provider UI condition failed: '+s);};
 const click=async text=>{await wait(`Array.from(document.querySelectorAll('button')).some(b=>b.innerText.includes(${JSON.stringify(text)})&&!b.disabled)`);await js(`Array.from(document.querySelectorAll('button')).find(b=>b.innerText.includes(${JSON.stringify(text)})).click()`);};
 const screenshot=async name=>{await new Promise(r=>setTimeout(r,200));const picture=await window.webContents.capturePage();if(picture.getSize().width<1000)throw new Error('The headless display did not render the window.');await fs.writeFile(path.join(out,name+'.png'),picture.toPNG());};
 try{
  await window.loadFile(path.resolve(__dirname,'../.build/provider-ui-fixture/tests/provider-ui.html'));
  await wait("document.body.innerText.includes('Continue with Anthropic')");await screenshot('provider-welcome');
  await click('Continue with OpenAI');await wait("window.providerFixture.calls.includes('login:chatgpt')&&document.body.innerText.includes('Complete provider sign-in')");
  checks.openai_onboarding=await js("window.providerFixture.calls.filter(c=>c==='login:chatgpt').length===1&&window.providerFixture.calls.includes('openLogin')");
  await click('Cancel login');await js("document.querySelector('details').open=true");await click('Use a device code');
  await wait("document.body.innerText.includes('FIXTURE-CODE')");checks.device_code=true;await screenshot('openai-device-code');
  await js('window.providerFixture.complete()');await wait("document.body.innerText.includes('fixture@example.invalid')");checks.openai_completion=true;
  await click('Sign out of provider');await wait("document.body.innerText.includes('OpenAI account is not connected')");checks.provider_logout=true;
  await click('Anthropic');await wait("window.providerFixture.calls.includes('login:claude')&&document.body.innerText.includes('Complete provider sign-in')");
  checks.provider_switch=await js("window.providerFixture.state().provider==='claude'");
  await js('window.providerFixture.fail()');await wait("document.body.innerText.includes('The provider refused access.')");checks.error_feedback=true;
  await click('Anthropic');await wait("document.querySelector('.login-pending details')!==null");await js("document.querySelector('.login-pending details').open=true");
  await js("(()=>{const i=document.querySelector('.login-pending input');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(i,'fixture-code');i.dispatchEvent(new Event('input',{bubbles:true}));})()");
  await click('Complete sign-in');await wait("document.body.innerText.includes('fixture@example.invalid')");checks.anthropic_code_completion=true;await screenshot('anthropic-connected');
  await click('Continue to workspace');await wait("document.body.innerText.includes('Workspace fixture')");checks.continue_workspace=true;
  await js('window.providerFixture.signOut()');await wait("document.body.innerText.includes('Continue with Anthropic')");
  await click('Continue with Anthropic');await wait("window.providerFixture.state().provider==='claude'&&document.body.innerText.includes('Complete provider sign-in')");
  checks.anthropic_onboarding=true;await screenshot('anthropic-login');
  checks.no_console_errors=errors.length===0;if(Object.values(checks).some(v=>!v))throw new Error('A provider UI check failed.');
  await fs.writeFile(path.join(out,'provider-ui.json'),JSON.stringify({status:'passed',checks,errors},null,2)+'\n');
 }catch(error){try{await screenshot('provider-failure');}catch{}await fs.writeFile(path.join(out,'provider-ui.json'),JSON.stringify({status:'failed',checks,errors,error:error.message,body:await js('document.body.innerText')},null,2)+'\n');process.exitCode=1;}
 finally{window.destroy();app.exit(process.exitCode||0);}
});
