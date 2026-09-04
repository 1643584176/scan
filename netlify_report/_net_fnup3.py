# -*- coding: utf-8 -*-
"""Netlify:zip 创建 deploy(含 functions 目录)探测函数上传格式"""
import http.client, ssl, gzip, brotli, sys, json, zipfile, io
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json'):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=60)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_A, 'Content-Type': ctype}
    payload = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn.request(method, path, body=payload, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

# zip: index.html + netlify/functions/probe1/index.js(源码形式)
FN = 'exports.handler = async () => ({ statusCode: 200, body: JSON.stringify({a:1}) });'
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.html', '<html>probe</html>')
    z.writestr('netlify/functions/probe1/index.js', FN)
zb = buf.getvalue()
print('zip size:', len(zb))

s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', raw_body=zb, ctype='application/zip')
print('create zip deploy:', s)
d = json.loads(raw) if s in (200, 201) else {}
DID = d.get('id')
print('deploy id:', DID)
print('state:', d.get('state'))
print('required_functions:', d.get('required_functions'))
print('functions:', json.dumps(d.get('functions'))[:300])
print('summary:', json.dumps({k: d.get(k) for k in ['summary', 'error_message']}))
if DID:
    open(r'D:\scan\netlify_report\_js\net_fn_deploy2.json', 'w').write(json.dumps({'deploy_id': DID}))
