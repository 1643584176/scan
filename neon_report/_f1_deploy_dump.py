# -*- coding: utf-8 -*-
"""Functions 面阶段1:deploy dump-env function(slug kf1)——先只列 env 变量名
零破坏:全部自建,结束 DELETE function。"""
import http.client, ssl, json, sys, io, zipfile, time, urllib.parse
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'
SLUG = 'kf1'

# --- 1. 构造 zip:根目录 index.mjs(纯 ESM,无 import)---
code = r'''export default {
  async fetch(request) {
    const names = Object.keys(process.env).sort();
    return new Response(JSON.stringify({ env_names: names }, null, 1), {
      headers: { 'content-type': 'application/json' },
    });
  }
};
'''
zbuf = io.BytesIO()
with zipfile.ZipFile(zbuf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.mjs', code)
zbytes = zbuf.getvalue()
print('zip bytes:', len(zbytes))

def req(method, path, body=None, hdrs=None, ctype=None):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    if ctype:
        h['Content-Type'] = ctype
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn.request(method, API_BASE + path, body=body, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status; conn.close()
    return st, raw

# --- 2. multipart deploy ---
boundary = '----kB0undary7f9d'
parts = []
parts.append(('--' + boundary).encode())
parts.append(b'Content-Disposition: form-data; name="zip"; filename="f.zip"\r\nContent-Type: application/zip\r\n\r\n')
parts.append(zbytes)
parts.append(('\r\n--' + boundary).encode())
parts.append(b'Content-Disposition: form-data; name="runtime"\r\n\r\nnodejs24')
parts.append(('\r\n--' + boundary + '--\r\n').encode())
body = b''.join(parts)

st, raw = req('POST', '/projects/%s/branches/%s/functions/%s/deployments' % (P, B, SLUG), body,
              ctype='multipart/form-data; boundary=' + boundary)
print('deploy -> %d | %s' % (st, raw.decode(errors='replace')[:400]))

# --- 3. 轮询 deployment 状态到 completed/failed ---
for i in range(20):
    st, raw = req('GET', '/projects/%s/branches/%s/functions/%s' % (P, B, SLUG))
    if st == 200:
        try:
            fn = json.loads(raw).get('function', {})
            print('fn state: %s | inv: %s' % (fn.get('current_deployment', {}).get('status'),
                                               fn.get('invocation_url', '')))
            depl = fn.get('current_deployment', {})
            if depl.get('status') in ('completed', 'failed'):
                print('full fn json:', json.dumps(fn, indent=1)[:1500])
                break
        except Exception as e:
            print('parse err', e, raw[:300])
    time.sleep(5)
