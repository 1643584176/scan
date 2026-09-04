# -*- coding: utf-8 -*-
"""dump hooks/types 元素完整结构 + url 校验边界测试"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'

def req(method, path, body=None, token=TOKEN_A, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if body is not None:
        h['Content-Type'] = 'application/json'
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

st, b = req('GET', '/api/v1/hooks/types')
d = json.loads(b)
print('count:', len(d))
for i, t in enumerate(d):
    keys = list(t.keys())
    print('[%d] keys=%s' % (i, keys))
    # 找名称类字段
    for k in ['type', 'name', 'id', 'key']:
        if k in t:
            print('    %s=%s' % (k, t[k]))
    # 打印 url 类型的完整字段
    has_url = any(f.get('name') == 'url' for f in t.get('fields', []))
    if has_url:
        print('    FULL JSON:', json.dumps(t)[:600])
print('done')
