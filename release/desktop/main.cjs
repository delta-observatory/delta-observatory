'use strict';
const { app, BrowserWindow, Menu, dialog, clipboard, ipcMain, shell } = require('electron');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { spawn } = require('node:child_process');
const { createInterface } = require('node:readline');
const { createServer } = require('./server.cjs');
const { importFiles } = require('./import.cjs');
const { AgentHost } = require('./agent.cjs');
const { utility } = require('./maintenance.cjs');

app.setName('Delta Observatory');
const argument = name => {
  const item = process.argv.find(value => value.startsWith(name + '='));
  return item ? item.slice(name.length + 1) : null;
};
let workspace = path.resolve(argument('--workspace') || path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local/share'), 'delta-observatory', 'workspace'));
const preferences=path.join(process.env.XDG_CONFIG_HOME||path.join(os.homedir(),'.config'),'delta-observatory','desktop.json');
const profile = workspace + '.electron-profile';
app.setPath('userData', profile);
const payload = path.join(__dirname, 'payload');
const host = argument('--review-host') || '127.0.0.1';
const requestedPort = Number(argument('--review-port') || 0);
const smokeOutput = argument('--smoke-output');
const productSmokeOutput = argument('--product-smoke-output');
const headless = process.argv.includes('--headless');
if (!['127.0.0.1', '0.0.0.0'].includes(host)) throw new Error('Unsupported review address.');
if (!Number.isInteger(requestedPort) || requestedPort < 0 || requestedPort > 65535) throw new Error('Invalid review port.');
if (headless) app.disableHardwareAcceleration();
// Keep Chromium's sandbox enabled. No renderer has Node or filesystem access.
app.enableSandbox();
if (!app.requestSingleInstanceLock()) app.exit(0);

let supervisor, server, window, readyRecord, stopping = false, allowQuit = false, exitCode = 0;
const consoleErrors = [];
let agentHost, loginUrl;
const AGENT_ACTIONS=new Set(['initialize','status','login','models','connect','send','interrupt','disconnect','logout']);

function startRuntime() {
  return new Promise((resolve, reject) => {
    const env = { PATH: '/usr/bin:/bin', LANG: 'C.UTF-8', PYTHONNOUSERSITE: '1', PYTHONDONTWRITEBYTECODE: '1' };
    supervisor = spawn(path.join(payload, 'python/bin/python3.12'), ['-s', path.join(__dirname, 'supervisor.py'),
      '--payload', payload, '--workspace', workspace, '--parent-pid', String(process.pid),...(!smokeOutput?['--public-exploration']:[])],
    { env, stdio: ['ignore', 'pipe', 'pipe'] });
    const timer = setTimeout(() => reject(new Error('The desktop startup deadline expired.')), 600000);
    createInterface({ input: supervisor.stdout }).on('line', line => {
      let message;
      try { message = JSON.parse(line); } catch { return; }
      if (message.type === 'ready') { clearTimeout(timer); resolve(message); }
      else if (message.type === 'error') { clearTimeout(timer); reject(new Error(message.message)); }
      else if (message.type === 'stage') console.log(message.message);
    });
    supervisor.stderr.on('data', chunk => process.stderr.write(chunk));
    supervisor.on('error', error => { clearTimeout(timer); reject(error); });
    supervisor.on('exit', code => {
      clearTimeout(timer);
      if (!readyRecord) reject(new Error(`The desktop services stopped during startup (${code}).`));
      else if (!stopping) { dialog.showErrorBox('Desktop service failure', `The local services stopped. Inspect ${path.join(workspace, 'logs')}.`); app.quit(); }
    });
  });
}

async function apiPost(route, body) {
  const token = (await fs.readFile(path.join(workspace, 'owner.token'), 'utf8')).trim();
  const response = await fetch(readyRecord.api_url + route, { method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body) });
  if (!response.ok) throw new Error(`The operation failed (${response.status}). ${await response.text()}`);
  return response.json();
}

async function importSelection() {
  const selection = await dialog.showOpenDialog(window, { title: 'Import TESS light curves into the workspace',
    properties: ['openFile', 'multiSelections'], filters: [{ name: 'TESS light curves', extensions: ['fits'] }] });
  if (selection.canceled) return;
  try {
    const policy=await utility(payload,workspace,'settings.py',['status']);
    const result = await importFiles(workspace, selection.filePaths, policy);
    await apiPost('/api/datasets/tess-spoc-light-curves/index');
    await dialog.showMessageBox(window, { message: 'Files imported into the separate workspace.',
      detail: `${result.copied} copied. ${result.unchanged} unchanged. The worker checks the files before analysis.` });
    window.reload();
  } catch (error) { dialog.showErrorBox('Import failed', error.message); }
}

function installMenu() {
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    { label: 'File', submenu: [
      { label: 'Import TESS light curves…', click: importSelection },
      { label: 'Refresh the observation index', click: async () => { try { await apiPost('/api/datasets/tess-spoc-light-curves/index'); } catch (error) { dialog.showErrorBox('Refresh failed', error.message); } } },
      { type: 'separator' }, { role: 'quit' },
    ] },
    { label: 'Edit', submenu: [{ role: 'undo' }, { role: 'redo' }, { type: 'separator' }, { role: 'cut' }, { role: 'copy' }, { role: 'paste' }, { role: 'selectAll' }] },
    { label: 'View', submenu: [{ role: 'reload' }, { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' }, { role: 'togglefullscreen' }] },
    { label: 'Workspace', submenu: [
      { label:'Workspace settings and recovery',click:()=>window.webContents.executeJavaScript("window.dispatchEvent(new Event('delta:settings-open'))") },
      { label: 'Workspace and services', click: () => dialog.showMessageBox(window, { message: 'Delta Observatory',
        detail: `Workspace: ${workspace}\nFrontend: ${window.webContents.getURL()}\nAPI: ${readyRecord.api_url}\n\nThis application uses its own database and files. This workspace supports exploratory investigations, approved downloads, and an optional managed agent.` }) },
      { label: 'Copy this workspace token', click: async () => { clipboard.writeText((await fs.readFile(path.join(workspace, 'owner.token'), 'utf8')).trim()); } },
    ] },
  ]));
}

async function rememberWorkspace(directory){
  await fs.mkdir(path.dirname(preferences),{recursive:true,mode:0o700});
  await fs.writeFile(preferences,JSON.stringify({workspace:directory})+'\n',{mode:0o600});
}
async function savePath(title,name){const selected=await dialog.showSaveDialog(window,{title,defaultPath:name,filters:[{name:'Delta package',extensions:['zip']}]});return selected.canceled?null:selected.filePath;}
async function openPackage(title){const selected=await dialog.showOpenDialog(window,{title,properties:['openFile'],filters:[{name:'Delta package',extensions:['zip']}]});return selected.canceled?null:selected.filePaths[0];}
async function reopen(directory){await rememberWorkspace(directory);app.relaunch({args:[...process.argv.slice(1).filter(a=>!a.startsWith('--workspace=')),'--workspace='+directory]});app.quit();return {workspace:directory};}
async function desktopOperation(action,params){
  const string=value=>{if(typeof value!=='string'||value.length>300)throw new Error('Invalid operation identifier.');return value;};
  if(action==='status')return utility(payload,workspace,'settings.py',['status']);
  if(action==='saveStorage')return utility(payload,workspace,'settings.py',['save','--reserve-bytes',String(params.reserve_bytes),'--maximum-bytes',String(params.maximum_bytes)]);
  if(action==='importFits'){await importSelection();return {complete:true};}
  if(action==='exportReproduction'){
    const selected=await savePath('Export a reproduction package','delta-reproduction.zip');if(!selected)return {cancelled:true};
    return utility(payload,workspace,'reproduction.py',['export','--run-id',string(params.run_id),'--path',selected,...(params.include_inputs===true?['--include-inputs']:[])]);
  }
  if(action==='importReproduction'){const selected=await openPackage('Import a reproduction package');return selected?utility(payload,workspace,'reproduction.py',['import','--path',selected]):{cancelled:true};}
  if(action==='listReproductions')return utility(payload,workspace,'reproduction.py',['list']);
  if(action==='prepareRepeat')return utility(payload,workspace,'reproduction.py',['prepare','--id',string(params.id)]);
  if(action==='compareRepeat')return utility(payload,workspace,'reproduction.py',['compare','--id',string(params.id),'--run-id',string(params.run_id)]);
  if(action==='backup'){const selected=await savePath('Save a workspace backup','delta-workspace-backup.zip');return selected?utility(payload,workspace,'recovery.py',['backup','--path',selected,...(params.include_inputs===false?['--without-observations']:[])]):{cancelled:true};}
  if(action==='restore'){
    const source=await openPackage('Select a workspace backup');if(!source)return {cancelled:true};
    const target=await dialog.showOpenDialog(window,{title:'Choose an empty restore directory',properties:['openDirectory','createDirectory']});if(target.canceled)return {cancelled:true};
    const result=await utility(payload,workspace,'recovery.py',['restore','--path',source,'--destination',target.filePaths[0]]);
    await reopen(result.workspace);return result;
  }
  if(action==='chooseWorkspace'){
    const target=await dialog.showOpenDialog(window,{title:'Choose an existing Delta workspace or an empty directory',properties:['openDirectory','createDirectory']});if(target.canceled)return {cancelled:true};
    const directory=target.filePaths[0],files=await fs.readdir(directory);
    if(files.length){let marker;try{marker=JSON.parse(await fs.readFile(path.join(directory,'workspace.json'),'utf8'));}catch{}if(marker?.kind!=='delta-desktop-prototype/1')throw new Error('Select a Delta workspace or an empty directory.');}
    return reopen(directory);
  }
  if(action==='diagnostics'){
    const target=await dialog.showSaveDialog(window,{title:'Export diagnostics without credentials or conversation text',defaultPath:'delta-diagnostics.json'});if(target.canceled)return {cancelled:true};
    const value=await utility(payload,workspace,'settings.py',['status']);await fs.writeFile(target.filePath,JSON.stringify(value,null,2)+'\n',{flag:'wx',mode:0o600});return {path:target.filePath};
  }
  if(action==='checkUpdate'){
    const response=await fetch('https://api.github.com/repos/delta-observatory/delta-observatory/releases/latest',{headers:{Accept:'application/vnd.github+json'},signal:AbortSignal.timeout(20000)});
    if(response.status===404)return {message:'No published desktop release is available.'};
    if(!response.ok)throw new Error('The release check failed ('+response.status+').');
    const value=await response.json();return {version:value.tag_name,url:value.html_url,message:'Release metadata only. Installation requires a separate installer action.'};
  }
  throw new Error('Unknown desktop operation.');
}

async function stop() {
  if (stopping) return;
  stopping = true;
  if (agentHost) await agentHost.close();
  if (server) { server.close(); server.closeAllConnections(); }
  if (supervisor && supervisor.exitCode === null) {
    await new Promise(resolve => {
      const timer = setTimeout(() => { console.error('Services need additional time to stop. Inspect the workspace logs.'); exitCode = 1; resolve(); }, 60000);
      supervisor.once('exit', () => { clearTimeout(timer); resolve(); });
      supervisor.kill('SIGTERM');
    });
  }
  await fs.rm(path.join(workspace, 'desktop.json'), { force: true });
  allowQuit = true;
  app.exit(exitCode);
}
app.on('before-quit', event => { if (!allowQuit) { event.preventDefault(); void stop(); } });
app.on('window-all-closed', () => app.quit());
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => app.quit());

app.whenReady().then(async () => {
  if(!argument('--workspace')){
    let saved;try{saved=JSON.parse(await fs.readFile(preferences,'utf8')).workspace;}catch{}
    if(saved)workspace=path.resolve(saved);
    else{const selection=await dialog.showOpenDialog({title:'Choose an empty directory for your Delta workspace',properties:['openDirectory','createDirectory']});if(selection.canceled){app.quit();return;}workspace=path.resolve(selection.filePaths[0]);await rememberWorkspace(workspace);}
  }
  app.setPath('userData',workspace+'.electron-profile');
  readyRecord = await startRuntime();
  server = createServer({ frontend: path.join(payload, 'frontend'), apiUrl: readyRecord.api_url });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(requestedPort, host, resolve); });
  const origin = `http://127.0.0.1:${server.address().port}`;
  await fs.writeFile(path.join(workspace, 'desktop.json'), JSON.stringify({ origin, host, pid: process.pid }) + '\n', { mode: 0o600 });
  // A screenshot needs a mapped window. The clean check supplies an isolated Xvfb display.
  window = new BrowserWindow({ width: 1440, height: 980, minWidth: 720, minHeight: 500, show: !headless || Boolean(smokeOutput || productSmokeOutput),
    title: 'Delta Observatory', backgroundColor: '#080c14',
    webPreferences: { preload: path.join(__dirname, 'preload.cjs'), nodeIntegration: false, contextIsolation: true, sandbox: true, webSecurity: true,
      backgroundThrottling: !headless } });
  window.on('page-title-updated', event => { event.preventDefault(); window.setTitle('Delta Observatory — separate workspace'); });
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  window.webContents.on('will-navigate', (event, target) => { if (new URL(target).origin !== origin) event.preventDefault(); });
  window.webContents.session.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  window.webContents.session.setPermissionCheckHandler(() => false);
  window.webContents.session.webRequest.onBeforeRequest((details, callback) => {
    callback({ cancel: /^https?:/.test(details.url) && new URL(details.url).origin !== origin });
  });
  window.webContents.on('console-message', details => {
    if (details.level === 'error') consoleErrors.push(details.message);
  });
  agentHost=new AgentHost({payload,workspace,apiUrl:readyRecord.api_url,onEvent:value=>{if(window&&!window.isDestroyed())window.webContents.send('delta:agent-event',value);}});
  ipcMain.handle('delta:agent',async(event,action,params={})=>{
    if(event.sender!==window.webContents||event.senderFrame!==window.webContents.mainFrame||new URL(event.senderFrame.url).origin!==origin)throw new Error('Invalid desktop caller.');
    if(action==='openLogin'){
      if(!loginUrl)throw new Error('Start login before opening the authorization page.');
      await shell.openExternal(loginUrl);return {opened:true};
    }
    if(!AGENT_ACTIONS.has(action))throw new Error('Unknown agent operation.');
    await agentHost.start();
    const result=await agentHost.call(action,params);
    if(action==='login'&&result.verificationUrl){
      const url=new URL(result.verificationUrl);
      if(url.protocol!=='https:'||!['auth.openai.com','chatgpt.com'].includes(url.hostname))throw new Error('The provider returned an unsupported login address.');
      loginUrl=url.href;
    }
    return result;
  });
  ipcMain.handle('delta:settings',async(event,action,params={})=>{
    if(event.sender!==window.webContents||event.senderFrame!==window.webContents.mainFrame||new URL(event.senderFrame.url).origin!==origin)throw new Error('Invalid desktop caller.');
    return desktopOperation(action,params);
  });
  installMenu();
  await window.loadURL(origin + '/desktop-start');
  const token = (await fs.readFile(path.join(workspace, 'owner.token'), 'utf8')).trim();
  await window.webContents.executeJavaScript(`localStorage.setItem('delta.token', ${JSON.stringify(token)});`);
  await window.loadURL(origin+(smokeOutput?'':'/?investigations'));
  console.log(`Desktop GUI: ${origin}`);
  if (productSmokeOutput) {
    await require('./checks/product-ui.cjs')({ window, output: productSmokeOutput, consoleErrors });
    app.quit();
  }
  if (smokeOutput) {
    await fs.mkdir(smokeOutput, { recursive: true });
    const deadline = Date.now() + 20000;
    let body = '';
    while (Date.now() < deadline) {
      body = await window.webContents.executeJavaScript('document.body.innerText');
      if (body.includes('desktop-owner') && /api\s+ok/.test(body) && !body.includes('Loading the result artifacts')) break;
      await new Promise(resolve => setTimeout(resolve, 250));
    }
    const fontsReady = await window.webContents.executeJavaScript(`document.fonts.ready.then(() =>
      document.fonts.check('400 12px "IBM Plex Sans"') && document.fonts.check('400 12px "IBM Plex Mono"'))`);
    await new Promise(resolve => setTimeout(resolve, 1000));
    const canvasPixels = await window.webContents.executeJavaScript(`Array.from(document.querySelectorAll('canvas')).map(canvas => {
      const context = canvas.getContext('2d');
      if (!context) return 0;
      const data = context.getImageData(0, 0, canvas.width, canvas.height).data;
      let lit = 0;
      for (let i = 0; i < data.length; i += 4) if (data[i + 3] && Math.max(data[i], data[i + 1], data[i + 2]) > 70) lit++;
      return lit;
    })`);
    const plotsReady = canvasPixels.length >= 2 && canvasPixels.every(count => count > 100);
    const report = { ready: body.includes('desktop-owner') && /api\s+ok/.test(body), consoleErrors, canvasPixels, plotsReady,
      runtime: readyRecord, electron: process.versions.electron, chromium: process.versions.chrome,
      os: os.release(), sandbox: window.webContents.getLastWebPreferences().sandbox, fontsReady };
    await fs.writeFile(path.join(smokeOutput, 'desktop.png'), (await window.webContents.capturePage()).toPNG());
    await fs.writeFile(path.join(smokeOutput, 'desktop.json'), JSON.stringify(report, null, 2) + '\n');
    if (!report.ready || !fontsReady || !plotsReady || consoleErrors.length) exitCode = 1;
    app.quit();
  }
}).catch(error => {
  console.error(error.message);
  if (!headless) dialog.showErrorBox('Delta desktop startup failed', error.message);
  exitCode = 1;
  app.quit();
});
