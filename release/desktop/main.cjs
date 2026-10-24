'use strict';
const { app, BrowserWindow, Menu, dialog, clipboard } = require('electron');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { spawn } = require('node:child_process');
const { createInterface } = require('node:readline');
const { createServer } = require('./server.cjs');
const { importFiles } = require('./import.cjs');

app.setName('Delta Observatory Prototype');
const argument = name => {
  const item = process.argv.find(value => value.startsWith(name + '='));
  return item ? item.slice(name.length + 1) : null;
};
const workspace = path.resolve(argument('--workspace') || path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local/share'), 'delta-observatory-prototype', 'workspace'));
const profile = workspace + '.electron-profile';
app.setPath('userData', profile);
const payload = path.join(__dirname, 'payload');
const host = argument('--review-host') || '127.0.0.1';
const requestedPort = Number(argument('--review-port') || 0);
const smokeOutput = argument('--smoke-output');
const headless = process.argv.includes('--headless');
if (!['127.0.0.1', '0.0.0.0'].includes(host)) throw new Error('Unsupported review address.');
if (!Number.isInteger(requestedPort) || requestedPort < 0 || requestedPort > 65535) throw new Error('Invalid review port.');
if (headless) app.disableHardwareAcceleration();
// Keep Chromium's sandbox enabled. No renderer has Node or filesystem access.
app.enableSandbox();
if (!app.requestSingleInstanceLock()) app.exit(0);

let supervisor, server, window, readyRecord, stopping = false, allowQuit = false, exitCode = 0;
const consoleErrors = [];

function startRuntime() {
  return new Promise((resolve, reject) => {
    const env = { PATH: '/usr/bin:/bin', LANG: 'C.UTF-8', PYTHONNOUSERSITE: '1', PYTHONDONTWRITEBYTECODE: '1' };
    supervisor = spawn(path.join(payload, 'python/bin/python3.12'), ['-s', path.join(__dirname, 'supervisor.py'),
      '--payload', payload, '--workspace', workspace, '--parent-pid', String(process.pid)],
    { env, stdio: ['ignore', 'pipe', 'pipe'] });
    const timer = setTimeout(() => reject(new Error('The prototype startup deadline expired.')), 90000);
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
      if (!readyRecord) reject(new Error(`The prototype services stopped during startup (${code}).`));
      else if (!stopping) { dialog.showErrorBox('Prototype service failure', `The separate services stopped. Inspect ${path.join(workspace, 'logs')}.`); app.quit(); }
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
  const selection = await dialog.showOpenDialog(window, { title: 'Import TESS light curves into the prototype',
    properties: ['openFile', 'multiSelections'], filters: [{ name: 'TESS light curves', extensions: ['fits'] }] });
  if (selection.canceled) return;
  try {
    const result = await importFiles(workspace, selection.filePaths);
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
    { label: 'Prototype', submenu: [
      { label: 'Workspace and services', click: () => dialog.showMessageBox(window, { message: 'Delta Observatory Prototype',
        detail: `Workspace: ${workspace}\nFrontend: ${window.webContents.getURL()}\nAPI: ${readyRecord.api_url}\n\nThis application uses its own database and files. Agent login and archive acquisition are outside P0.` }) },
      { label: 'Copy this workspace token', click: async () => { clipboard.writeText((await fs.readFile(path.join(workspace, 'owner.token'), 'utf8')).trim()); } },
    ] },
  ]));
}

async function stop() {
  if (stopping) return;
  stopping = true;
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
  readyRecord = await startRuntime();
  server = createServer({ frontend: path.join(payload, 'frontend'), apiUrl: readyRecord.api_url });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(requestedPort, host, resolve); });
  const origin = `http://127.0.0.1:${server.address().port}`;
  await fs.writeFile(path.join(workspace, 'desktop.json'), JSON.stringify({ origin, host, pid: process.pid }) + '\n', { mode: 0o600 });
  // A screenshot needs a mapped window. The clean check supplies an isolated Xvfb display.
  window = new BrowserWindow({ width: 1440, height: 980, minWidth: 720, minHeight: 500, show: !headless || Boolean(smokeOutput),
    title: 'Delta Observatory Prototype', backgroundColor: '#080c14',
    webPreferences: { nodeIntegration: false, contextIsolation: true, sandbox: true, webSecurity: true,
      backgroundThrottling: !headless } });
  window.on('page-title-updated', event => { event.preventDefault(); window.setTitle('Delta Observatory Prototype — separate workspace'); });
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
  installMenu();
  await window.loadURL(origin + '/desktop-start');
  const token = (await fs.readFile(path.join(workspace, 'owner.token'), 'utf8')).trim();
  await window.webContents.executeJavaScript(`localStorage.setItem('delta.token', ${JSON.stringify(token)});`);
  await window.loadURL(origin);
  console.log(`Prototype GUI: ${origin}`);
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
  if (!headless) dialog.showErrorBox('Delta prototype startup failed', error.message);
  exitCode = 1;
  app.quit();
});
