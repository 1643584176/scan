'use strict';
// probe10:网络拓扑 + DNS 内部域名解析 + 本地端口探测
const fs = require('fs');
const dns = require('dns');
const net = require('net');

function readFile(p) {
  try { return fs.readFileSync(p, 'utf8'); } catch (e) { return '(err ' + e.code + ')'; }
}

function tcpProbe(host, port, timeoutMs) {
  return new Promise((res) => {
    const s = net.connect({ host, port, timeout: timeoutMs });
    const done = (ok) => { try { s.destroy(); } catch (e) {} res(ok); };
    s.on('connect', () => done(true));
    s.on('timeout', () => done(false));
    s.on('error', () => done(false));
  });
}

exports.handler = async (event) => {
  const out = {};
  const q = event.queryStringParameters || {};

  if (q.mode === 'dns') {
    const hosts = (q.hosts || '').split(',').filter(Boolean);
    const r = {};
    for (const h of hosts) {
      try {
        const a = await new Promise((res, rej) => dns.resolve4(h, (e, x) => e ? rej(e) : res(x)));
        r[h] = a;
      } catch (e) {
        r[h] = 'FAIL:' + (e.code || e.message);
      }
    }
    return { statusCode: 200, headers: { 'content-type': 'application/json' }, body: JSON.stringify(r) };
  }

  if (q.mode === 'tcp') {
    const r = {};
    for (const hp of (q.targets || '').split(',').filter(Boolean)) {
      const i = hp.lastIndexOf(':');
      const host = hp.slice(0, i); const port = parseInt(hp.slice(i + 1), 10);
      r[hp] = await tcpProbe(host, port, parseInt(q.timeout || '3000', 10));
    }
    return { statusCode: 200, headers: { 'content-type': 'application/json' }, body: JSON.stringify(r) };
  }

  // 默认:全面信息
  out.resolv = readFile('/etc/resolv.conf');
  out.hosts = readFile('/etc/hosts');
  out.route = readFile('/proc/net/route');
  out.fib = readFile('/proc/net/fib_trie').slice(0, 2000);
  out.arp = readFile('/proc/net/arp');
  out.tcpConn = readFile('/proc/net/tcp').slice(0, 2500);
  out.iface = readFile('/proc/net/dev');
  out.envKeys = Object.keys(process.env).filter(k => /NETLIFY|SITE|URL|ACCOUNT|DEPLOY|FUNCTION/.test(k)).map(k => k + '=' + process.env[k]);
  out.free = readFile('/proc/1/cmdline').replace(/\0/g, ' ');

  const cand = [
    'lambda-events.services.netlify.com',
    'jigsaw.services-prod.nsvcs.net',
    'services-prod.nsvcs.net',
    'nsvcs.net',
    'api-create.services.netlify.com',
    'identeer.services.netlify.com',
    'socketeer.services.netlify.com',
    'analytics.services.netlify.com',
    'metadata.netlify.internal',
    'functions.netlify.internal',
    'secrets.netlify.internal',
    'netlify.internal',
    'telemetry.netlify.internal',
    'events.netlify.internal',
    'api.netlify.internal',
    'int-api.netlify.com',
    'functions.internal.netlify.com',
    'telemetry.services.netlify.com',
  ];
  const dnsRes = {};
  await Promise.all(cand.map(async (h) => {
    try {
      const a = await new Promise((res, rej) => dns.resolve4(h, (e, x) => e ? rej(e) : res(x)));
      dnsRes[h] = a;
    } catch (e) { dnsRes[h] = 'FAIL:' + (e.code || e.message); }
  }));
  out.dns = dnsRes;
  return { statusCode: 200, headers: { 'content-type': 'application/json' }, body: JSON.stringify(out) };
};
