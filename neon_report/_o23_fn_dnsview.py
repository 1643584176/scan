# -*- coding: utf-8 -*-
"""函数内部 DNS 视图测试:候选内部名解析(函数内) vs 外部对照"""
import http.client, ssl, json, re, html, os, sys, time, io, zipfile, uuid, socket

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']

# 外部对照解析
EXT_HOSTS = [
    'otel.c-1.us-east-2.aws.neon.build',
    'br-wandering-field-w2ob6mpn.storage.c-1.us-east-2.aws.neon.build',
    'br-wandering-field-w2ob6mpn-api.ai.c-1.us-east-2.aws.neon.build',
    'pg.c-1.us-east-2.aws.neon.build', 'proxy.c-1.us-east-2.aws.neon.build',
    'compute.c-1.us-east-2.aws.neon.build', 'metadata.c-1.us-east-2.aws.neon.build',
    'functions.c-1.us-east-2.aws.neon.build', 'registry.c-1.us-east-2.aws.neon.build',
    'builder.c-1.us-east-2.aws.neon.build', 'scheduler.c-1.us-east-2.aws.neon.build',
    'console.c-1.us-east-2.aws.neon.build', 'auth.c-1.us-east-2.aws.neon.build',
    'data.c-1.us-east-2.aws.neon.build', 'minio.c-1.us-east-2.aws.neon.build',
    'vault.c-1.us-east-2.aws.neon.build', 'etcd.c-1.us-east-2.aws.neon.build',
    'kubernetes.c-1.us-east-2.aws.neon.build', 'api.c-1.us-east-2.aws.neon.build',
    'storage.c-1.us-east-2.aws.neon.build', 'otel.internal', 'console.internal',
    'neon.internal', 'pg.internal', 'compute.internal', 'functions.internal',
]
print('=== 外部 DNS 对照 ===', flush=True)
for h in EXT_HOSTS:
    try:
        ip = socket.gethostbyname(h)
        if not ip.startswith(('10.', '172.', '192.168.')):
            print('pub %s -> %s' % (h, ip), flush=True)
        else:
            print('RFC1918 %s -> %s  <<<<<<' % (h, ip), flush=True)
    except Exception:
        pass

# 函数内解析(完整候选清单)
CANDS = ['pg', 'proxy', 'compute', 'metadata', 'functions', 'registry', 'builder',
         'scheduler', 'console', 'auth', 'data', 'minio', 'vault', 'etcd', 'kubernetes',
         'api', 'storage', 'otel', 'control-plane', 'controlplane', 'platform', 'neon',
         'image', 'images', 'docker', 'cri', 'containerd', 'kubelet', 'node', 'gateway',
         'ingress', 'lb', 'load', 'balancer', 'router', 'proxy2', 'pgbouncer', 'pgb',
         'postgres', 'postgresql', 'storage-api', 's3', 'buckets', 'ai', 'ai-gateway',
         'llm', 'openai', 'telemetry', 'metrics', 'trace', 'log', 'logs', 'fluent',
         'vector', 'loki', 'prometheus', 'grafana', 'tempo', 'jaeger', 'otel-collector',
         'collector', 'otelcol', 'opentelemetry']
print('external done', flush=True)

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
    conn3 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=90)
    hdrs = {'Cookie': '; '.join(parts), 'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    if ctype:
        hdrs['Content-Type'] = ctype
    data = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn3.request(method, path, body=data, headers=hdrs)
    r3 = conn3.getresponse()
    out = r3.read().decode('utf-8', 'ignore')
    conn3.close()
    return r3.status, out

# 先获取 csrf(ctl_req 简化版需要)
def csrf_cookie():
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r = conn.getresponse()
    r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
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
    return '; '.join(parts), csrf

PROBE_TMPL = r'''const sleep = (ms) => new Promise(r => setTimeout(r, ms));
async function probe() {
  await sleep(1000);
  const hosts = __HOSTS__;
  const seen = new Set();
  try {
    const dns = await import('node:dns');
    for (const h of hosts) {
      try {
        const a = await dns.promises.resolve4(h);
        const hit = a.filter(x => /^(10\.|172\.|192\.168\.)/.test(x)).length > 0;
        if (hit) console.log('P4 RFC1918 ' + h + ' => ' + JSON.stringify(a));
        else if (a.length) console.log('P4 pub ' + h + ' => ' + JSON.stringify(a));
      } catch (e) { /* NXDOMAIN */ }
    }
    // 我们已知域的服务发现:尝试相邻命名
    for (const svc of __SVC__) {
      for (const dom of ['c-1.us-east-2.aws.neon.build']) {
        const h = svc + '.' + dom;
        try {
          const a = await dns.promises.resolve4(h);
          const hit = a.filter(x => /^(10\.|172\.|192\.168\.)/.test(x)).length > 0;
          console.log('P4 ' + (hit ? 'RFC1918' : 'pub') + ' svc ' + h + ' => ' + JSON.stringify(a));
        } catch (e) {}
      }
    }
  } catch (e) { console.log('P4 import ERR ' + e.message); }
  console.log('P4 done');
}
probe();
export default { fetch: async (req) => new Response('ok') };
'''

svcs = ['pg', 'proxy', 'compute', 'metadata', 'functions', 'registry', 'builder', 'scheduler',
        'console', 'auth', 'data', 'minio', 'vault', 'etcd', 'kubernetes', 'api', 'storage', 'otel',
        'control-plane', 'platform', 'image', 'gateway', 'ingress', 'lb', 'router', 'pgbouncer',
        'postgres', 's3', 'ai', 'ai-gateway', 'telemetry', 'metrics', 'logs', 'loki', 'prometheus',
        'grafana', 'collector', 'otel-collector', 'compute-node', 'proxy-node', 'storage-node']
PROBE = PROBE_TMPL.replace('__HOSTS__', json.dumps(EXT_HOSTS)).replace('__SVC__', json.dumps(svcs))

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', PROBE)
    z.writestr('package.json', '{"name":"probe4","type":"module","main":"index.js"}')
buf.seek(0)
zip_bytes = buf.read()

SLUG = 'secprb4' + uuid.uuid4().hex[:6]
FP = '/projects/%s/branches/%s/functions' % (PID, BID)
boundary = '----b' + uuid.uuid4().hex
body = (('--' + boundary + '\r\nContent-Disposition: form-data; name="zip"; filename="b.zip"\r\nContent-Type: application/zip\r\n\r\n').encode()
        + zip_bytes + b'\r\n'
        + ('--' + boundary + '\r\nContent-Disposition: form-data; name="runtime"\r\n\r\nnodejs24\r\n').encode()
        + ('--' + boundary + '--\r\n').encode())
ck, csrf = csrf_cookie()
conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=90)
hdrs = {'Cookie': ck, 'Content-Type': 'multipart/form-data; boundary=' + boundary,
        'X-CSRF-Token': csrf, 'User-Agent': 'Mozilla/5.0'}
hdrs.update(HEADERS_TEST)
conn.request('POST', API_BASE + FP + '/' + SLUG + '/deployments', body=body, headers=hdrs)
r = conn.getresponse()
raw = r.read().decode('utf-8', 'ignore')
conn.close()
print('deploy -> %d %s' % (r.status, raw[:200]), flush=True)

seen = set()
t0 = time.time()
while time.time() - t0 < 180:
    time.sleep(5)
    ck2, csrf2 = csrf_cookie()
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=90)
    hdrs = {'Cookie': ck2, 'Content-Type': 'application/json', 'X-CSRF-Token': csrf2,
            'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    conn.request('POST', API_BASE + '/projects/%s/branches/%s/logs/query' % (PID, BID),
                 body=json.dumps({'since': '10m', 'body_contains': 'P4 '}).encode(), headers=hdrs)
    r2 = conn.getresponse()
    raw2 = r2.read().decode('utf-8', 'ignore')
    conn.close()
    try:
        for lg in json.loads(raw2).get('logs', []):
            msg = lg.get('message') or lg.get('line') or str(lg)
            if isinstance(msg, str) and msg.startswith('P4 ') and msg not in seen:
                seen.add(msg)
                print('LOG: %s' % msg[:500], flush=True)
    except Exception:
        pass
    if 'P4 done' in ' '.join(seen):
        break
print('rows:', len(seen), flush=True)

ck3, csrf3 = csrf_cookie()
conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
hdrs = {'Cookie': ck3, 'Content-Type': 'application/json', 'X-CSRF-Token': csrf3,
        'User-Agent': 'Mozilla/5.0'}
hdrs.update(HEADERS_TEST)
conn.request('DELETE', API_BASE + FP + '/' + SLUG, headers=hdrs)
r3 = conn.getresponse()
r3.read()
conn.close()
print('cleanup -> %d' % r3.status, flush=True)
