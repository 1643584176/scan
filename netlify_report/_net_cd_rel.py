# -*- coding: utf-8 -*-
"""删除站点后 custom_domain 是否释放? B 账号(剩余配额~2)
实验: B 建临时站绑 rel-{r}.com -> 删站 -> 再建站绑同域 -> unique or accept?
"""
import http.client, ssl, gzip, brotli, json, sys, time, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B

ctx = ssl.create_default_context()
TOK = TOKEN_B

def req(method, path, body=None, timeout=30):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + TOK}
    b = json.dumps(body).encode() if body is not None else None
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

def mk():
    name = 'sec-rel-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    st, b = req('POST', '/api/v1/sites', {'name': name})
    try:
        return st, json.loads(b).get('id')
    except Exception:
        return st, b[:100]

def patch_cd(sid, val):
    st, b = req('PATCH', '/api/v1/sites/' + sid, {'custom_domain': val})
    try:
        j = json.loads(b)
        if st == 200:
            return st, 'ACCEPT cd=%r' % j.get('custom_domain')
        return st, str(j.get('errors') or j.get('message'))[:130]
    except Exception:
        return st, b[:130]

def delete(sid):
    st, b = req('DELETE', '/api/v1/sites/' + sid)
    return st

r = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
DOM = 'rel-%s.com' % r
print('DOM =', DOM)

print('== 1. B 建站 S1 绑 DOM ==')
st, s1 = mk()
print('mk S1:', st, s1)
if isinstance(s1, str):
    print('patch:', patch_cd(s1, DOM))

print('== 2. 删除 S1 ==')
print('del S1:', delete(s1))

time.sleep(3)
print('== 3. B 再建站 S2 绑同一 DOM(看是否释放) ==')
st, s2 = mk()
print('mk S2:', st, s2)
if isinstance(s2, str):
    print('patch:', patch_cd(s2, DOM))

print('== 4. 清理 S2 ==')
if isinstance(s2, str):
    print('del S2:', delete(s2))
print('done')
