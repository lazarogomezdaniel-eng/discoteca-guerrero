const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const ROOT = path.resolve(__dirname);

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.glb': 'model/gltf-binary',
  '.gltf': 'model/gltf+json',
  '.bin': 'application/octet-stream',
  '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav',
};

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  let reqPath = decodeURIComponent(req.url.split('?')[0]);
  if (reqPath === '/' || reqPath === '') reqPath = '/index.html';
  console.log('[REQ]', req.method, reqPath);

  const safePath = path.normalize(reqPath).replace(/^(\.\.[\/\\])+/, '');
  const filePath = path.join(ROOT, safePath);

  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not Found: ' + reqPath);
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    const range = req.headers.range;
    if (range) {
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : stats.size - 1;
      const chunkSize = (end - start) + 1;
      const fileStream = fs.createReadStream(filePath, { start, end });

      fileStream.on('error', (streamErr) => {
        console.error('[Stream Error]', streamErr.message);
        if (!res.headersSent) res.writeHead(500);
        res.end();
      });
      res.on('close', () => {
        fileStream.destroy();
      });

      res.writeHead(206, {
        'Content-Range': `bytes ${start}-${end}/${stats.size}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunkSize,
        'Content-Type': contentType,
      });
      fileStream.pipe(res);
    } else {
      const fileStream = fs.createReadStream(filePath);

      fileStream.on('error', (streamErr) => {
        console.error('[Stream Error]', streamErr.message);
        if (!res.headersSent) res.writeHead(500);
        res.end();
      });
      res.on('close', () => {
        fileStream.destroy();
      });

      res.writeHead(200, {
        'Content-Length': stats.size,
        'Content-Type': contentType,
        'Accept-Ranges': 'bytes'
      });
      fileStream.pipe(res);
    }
  });
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`⚠️ Port ${PORT} is already in use. Waiting or retry...`);
  } else {
    console.error('[Server Error]', err);
  }
});

process.on('uncaughtException', (err) => {
  console.error('[Uncaught Exception]', err.message);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Guerrero 3D Server running at http://localhost:${PORT}/index.html`);
});
