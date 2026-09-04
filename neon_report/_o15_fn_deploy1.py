# -*- coding: utf-8 -*-
"""Functions 首次部署:构造 zip(index.js handler) -> multipart 上传 -> 轮询状态 -> 调用 invocation_url
zip 猜测:CLI esbuild 产物单文件;先试纯 ESM index.js + package.json type=module"""
import http.client, ssl, json, re, html, os, sys, time, io, zipfile, uuid

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']

def ctl_req(method, path, body=None, ctype='application/json', raw_body=None, extra=None):
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
    conn3 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    hdrs = {'Cookie': '; '.join(parts), 'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    if ctype:
        hdrs['Content-Type'] = ctype
    if csrf:
        hdrs['X-CSRF-Token'] = csrf
    if extra:
        hdrs.update(extra)
    data = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn3.request(method, path, body=data, headers=hdrs)
    r3 = conn3.getresponse()
    out = r3.read().decode('utf-8', 'ignore')
    conn3.close()
    return r3.status, out

# --- zip 构造:handler 返回环境信息(部署后用) ---
HANDLER = r"""export default {
  fetch: async (request) => {
    const out = {
      method: request.method,
      url: request.url,
      headers: Object.fromEntries(request.headers.entries()),
      envs: Object.keys(process.env).filter(k => /NEON|PG|DATABASE|AWS|HOST|SECRET|TOKEN|KEY/i.test(k)).map(k => k + '=' + (process.env[k] || '').slice(0, 120)),
    };
    return new Response(JSON.stringify(out, null, 1), { headers: { 'content-type': 'application/json' } });
  }
};
"""

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', HANDLER)
    z.writestr('package.json', '{"name":"fn-probe","type":"module","main":"index.js"}')
buf.seek(0)
zip_bytes = buf.read()
print('zip size:', len(zip_bytes), flush=True)

SLUG = 'secfn' + uuid.uuid4().hex[:8]
FP = '/projects/%s/branches/%s/functions' % (PID, BID)
boundary = '----b' + uuid.uuid4().hex
parts = []
def mp_field(name, value, is_file=False):
    global parts
    if is_file:
        parts.append(('--' + boundary + '\r\nContent-Disposition: form-data; name="%s"; filename="bundle.zip"\r\nContent-Type: application/zip\r\n\r\n' % name).encode() + value + b'\r\n')
    else:
        parts.append(('--' + boundary + '\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (name, value)).encode())

mp_field('zip', zip_bytes, is_file=True)
mp_field('runtime', 'nodejs24')
body = b''.join(parts) + ('--' + boundary + '--\r\n').encode()

print('=== [1] deploy (multipart zip) ===', flush=True)
st, raw = ctl_req('POST', API_BASE + FP + '/' + SLUG + '/deployments', None,
                  ctype='multipart/form-data; boundary=' + boundary, raw_body=body)
print('deploy -> %d %s' % (st, raw[:400].replace('\n', ' ')), flush=True)

print('\n=== [2] 轮询 function 状态 ===', flush=True)
fn = None
for i in range(12):
    time.sleep(4)
    st, raw = ctl_req('GET', API_BASE + FP + '/' + SLUG)
    if st == 200:
        d = json.loads(raw)
        fn = d.get('function', {})
        cd = fn.get('current_deployment', {})
        print('[%d] status=%s error=%s' % (i, cd.get('status'), (cd.get('error') or '')[:150]), flush=True)
        if cd.get('status') in ('completed', 'failed'):
            break
    else:
        print('[%d] GET -> %d %s' % (i, st, raw[:200]), flush=True)

if fn:
    print('\nfunction:', json.dumps({k: fn.get(k) for k in ['id', 'slug', 'name', 'invocation_url']}), flush=True)
    iurl = fn.get('invocation_url', '')
    if iurl:
        print('\n=== [3] 调用 invocation_url ===', flush=True)
        try:
            conn = http.client.HTTPSConnection(iurl.split('//')[1].split('/')[0], context=ctx, timeout=30)
            conn.request('GET', '/', headers={'User-Agent': 'curl/8'})
            r = conn.getresponse()
            data = r.read().decode('utf-8', 'replace')
            print('status %d' % r.status, flush=True)
            print(data[:1200], flush=True)
            conn.close()
        except Exception as e:
            print('call err:', e, flush=True)
