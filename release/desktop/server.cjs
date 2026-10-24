'use strict';
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2' };

function staticPath(root, requestPath) {
  let decoded;
  try { decoded = decodeURIComponent(requestPath.split('?')[0]); } catch { return null; }
  if (decoded.includes('\0') || decoded.includes('\\') || decoded.split('/').includes('..')) return null;
  const filename = path.resolve(root, '.' + decoded);
  return filename.startsWith(path.resolve(root) + path.sep) ? filename : null;
}

function createServer({ frontend, apiUrl }) {
  const upstream = new URL(apiUrl);
  if (upstream.protocol !== 'http:' || upstream.hostname !== '127.0.0.1') throw new Error('The API must use local loopback.');
  return http.createServer((request, response) => {
    response.setHeader('X-Content-Type-Options', 'nosniff');
    response.setHeader('Referrer-Policy', 'no-referrer');
    response.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; object-src 'none'");
    if (/^\/(api|gui-api)\//.test(request.url)) {
      const headers = { ...request.headers, host: upstream.host };
      delete headers.connection;
      const proxied = http.request({ hostname: upstream.hostname, port: upstream.port, method: request.method,
        path: request.url, headers }, result => {
        response.writeHead(result.statusCode, result.headers);
        result.pipe(response);
      });
      proxied.on('error', () => { if (!response.headersSent) response.writeHead(502); response.end('The desktop API is unavailable.'); });
      request.on('aborted', () => proxied.destroy());
      request.pipe(proxied);
      return;
    }
    if (!['GET', 'HEAD'].includes(request.method)) { response.writeHead(405); response.end(); return; }
    if (request.url === '/desktop-start') {
      response.setHeader('Content-Type', TYPES['.html']);
      response.end('<!doctype html><title>Delta Observatory</title><p>Starting the separate workspace.</p>');
      return;
    }
    const filename = staticPath(frontend, request.url.split('?')[0] === '/' ? '/index.html' : request.url);
    if (!filename) { response.writeHead(400); response.end('Invalid path.'); return; }
    fs.stat(filename, (error, stat) => {
      if (error || !stat.isFile()) { response.writeHead(404); response.end('File not found.'); return; }
      response.setHeader('Content-Type', TYPES[path.extname(filename)] || 'application/octet-stream');
      response.setHeader('Content-Length', stat.size);
      response.setHeader('Cache-Control', 'no-cache');
      if (request.method === 'HEAD') response.end();
      else fs.createReadStream(filename).on('error', () => response.destroy()).pipe(response);
    });
  });
}
module.exports = { createServer, staticPath };
