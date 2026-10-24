'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const { createServer, staticPath } = require('../desktop/server.cjs');
const { importFiles } = require('../desktop/import.cjs');

test('the static server rejects encoded traversal and never exposes runtime files', async t => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'delta-static-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const front = path.join(root, 'frontend'); await fs.mkdir(front);
  await fs.writeFile(path.join(front, 'index.html'), 'Delta');
  await fs.writeFile(path.join(root, 'owner.token'), 'private');
  assert.equal(staticPath(front, '/%2e%2e/owner.token'), null);
  assert.equal(staticPath(front, '/%00'), null);
  assert.equal(staticPath(front, '/..%5cowner.token'), null);
  const upstream = http.createServer((req, res) => res.end(req.headers.authorization || 'anonymous'));
  await new Promise(resolve => upstream.listen(0, '127.0.0.1', resolve));
  const server = createServer({ frontend: front, apiUrl: `http://127.0.0.1:${upstream.address().port}` });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => { server.closeAllConnections(); server.close(); upstream.closeAllConnections(); upstream.close(); });
  const origin = `http://127.0.0.1:${server.address().port}`;
  assert.equal(await (await fetch(origin)).text(), 'Delta');
  assert.equal((await fetch(origin + '/owner.token')).status, 404);
  assert.equal(await (await fetch(origin + '/api/me')).text(), 'anonymous');
  assert.equal(await (await fetch(origin + '/api/me', { headers: { Authorization: 'Bearer example' } })).text(), 'Bearer example');
});

test('imports preserve originals, refuse replacement, reject symlinks, and do not duplicate files', async t => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'delta-import-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const workspace = path.join(root, 'workspace');
  await fs.mkdir(path.join(workspace, 'raw/tess-spoc-light-curves'), { recursive: true });
  await fs.writeFile(path.join(workspace, 'workspace.json'), JSON.stringify({ kind: 'delta-desktop-prototype/1' }));
  const source = path.join(root, 'sample_lc.fits'); await fs.writeFile(source, 'sample');
  assert.deepEqual(await importFiles(workspace, [source]), { copied: 1, unchanged: 0 });
  assert.deepEqual(await importFiles(workspace, [source]), { copied: 0, unchanged: 1 });
  assert.equal(await fs.readFile(source, 'utf8'), 'sample');
  await fs.writeFile(source, 'different');
  await assert.rejects(importFiles(workspace, [source]), /different file/);
  assert.equal(await fs.readFile(path.join(workspace, 'raw/tess-spoc-light-curves/sample_lc.fits'), 'utf8'), 'sample');
  const link = path.join(root, 'linked_lc.fits'); await fs.symlink(source, link);
  await assert.rejects(importFiles(workspace, [link]), /regular files/);
  await assert.rejects(importFiles(workspace, [source, source]), /different file|repeated/);
});
