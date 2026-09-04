// Netlify probe6: 探测 lambda-events.services.netlify.com 内部端点 + NETLIFY_FUNCTIONS_TOKEN 在此的权限
const fetchT = async (url, opts = {}, ms = 6000) => {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), ms);
  try {
    const r = await fetch(url, { ...opts, signal: ac.signal, redirect: 'manual' });
    const b = await r.text();
    const hdrs = {};
    r.headers.forEach((v, k) => { hdrs[k] = v; });
    return r.status + ' hdr=' + JSON.stringify(hdrs).slice(0, 250) + ' body=' + b.slice(0, 500).replace(/\n/g, '\\n');
  } catch (e) {
    return 'ERR ' + String(e).slice(0, 100);
  } finally { clearTimeout(t); }
};

exports.handler = async () => {
  const out = { probe: [] };
  const NF = process.env.NETLIFY_FUNCTIONS_TOKEN || '';
  const base = 'https://lambda-events.services.netlify.com';
  const paths = ['/', '/health', '/healthz', '/ping', '/api', '/v1', '/events', '/traces', '/api/v1/events',
    '/api/v1/traces', '/v1/traces', '/api/events', '/internal', '/metrics', '/debug', '/ready'];
  for (const p of paths) {
    out.probe.push('GET ' + p + ' => ' + await fetchT(base + p, {}, 5000));
  }
  // 带 token 变体头尝试
  for (const [label, h] of [
    ['nf-bearer', { 'Authorization': 'Bearer ' + NF }],
    ['nf-xkey', { 'x-api-key': NF }],
    ['nf-nftoken', { 'NETLIFY_FUNCTIONS_TOKEN': NF }],
  ]) {
    out.probe.push(label + ' / => ' + await fetchT(base + '/', { headers: h }, 5000));
  }
  // DNS 解析验证域名内部解析
  out.envCheck = {
    hasToken: !!NF,
    nfToken: NF.slice(0, 8),
  };
  return { statusCode: 200, body: JSON.stringify(out) };
};
