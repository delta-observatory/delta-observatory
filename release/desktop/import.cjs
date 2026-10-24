'use strict';
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const { createReadStream, constants } = require('node:fs');

async function digest(filename) {
  const hash = crypto.createHash('sha256');
  for await (const chunk of createReadStream(filename)) hash.update(chunk);
  return hash.digest('hex');
}

async function importFiles(workspace, files) {
  if (!files.length || files.length > 128) throw new Error('Select between 1 and 128 light-curve files.');
  const marker = JSON.parse(await fs.readFile(path.join(workspace, 'workspace.json'), 'utf8'));
  if (marker.kind !== 'delta-desktop-prototype/1') throw new Error('The destination is not a prototype workspace.');
  const destination = path.join(workspace, 'raw', 'tess-spoc-light-curves');
  const entries = [];
  let total = 0;
  const names = new Set();
  for (const filename of files) {
    const stat = await fs.lstat(filename);
    const name = path.basename(filename);
    if (!stat.isFile() || stat.isSymbolicLink() || !name.endsWith('_lc.fits')) throw new Error('Import regular files whose names end in _lc.fits.');
    if (names.has(name)) throw new Error('The selection contains repeated filenames.');
    names.add(name);
    total += stat.size;
    if (total > 2 * 1024 ** 3) throw new Error('This prototype accepts at most 2 GiB in one import.');
    const sha = await digest(filename);
    const target = path.join(destination, name);
    let exists = false;
    try {
      const present = await fs.lstat(target);
      if (!present.isFile() || present.isSymbolicLink() || await digest(target) !== sha) throw new Error(`A different file already uses this name: ${name}`);
      exists = true;
    } catch (error) { if (error.code !== 'ENOENT') throw error; }
    entries.push({ filename, target, sha, exists });
  }
  const capacity = await fs.statfs(destination);
  if (Number(capacity.bavail) * Number(capacity.bsize) < total + 512 * 1024 ** 2) throw new Error('The workspace needs more free space.');
  let copied = 0;
  for (const entry of entries) {
    if (entry.exists) continue;
    const temporary = entry.target + '.' + crypto.randomUUID() + '.importing';
    try {
      await fs.copyFile(entry.filename, temporary, constants.COPYFILE_EXCL);
      await fs.chmod(temporary, 0o600);
      if (await digest(temporary) !== entry.sha) throw new Error('An input changed during import.');
      // link is atomic and refuses an existing destination. The index never sees a partial FITS file.
      await fs.link(temporary, entry.target);
      copied += 1;
    } finally { await fs.rm(temporary, { force: true }); }
  }
  return { copied, unchanged: entries.length - copied };
}
module.exports = { digest, importFiles };
