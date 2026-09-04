# -*- coding: utf-8 -*-
"""邀请 B 进 A team(Developer) + 观察邀请流程; 先清理 73be2516 站点"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()

def req(method, path, body=None, token=TOKEN_A, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
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

def probe(tag, m, p, body=None, tok=TOKEN_A):
    st, b = req(m, p, body, tok)
    print('%-60s %s | %s' % (tag, st, b[:300].replace('\n', ' ')))
    return st, b

print('== 0. 清理误建站点 ==')
probe('DELETE 73be2516', 'DELETE', '/api/v1/sites/73be2516-387e-4e77-9623-a332438769cd')

print()
print('== 1. 邀请 B(Developer)进 A team ==')
# 常见字段组合逐个试
for body in [
    {'email': '729488839@qq.com'},
    {'email': '729488839@qq.com', 'role': 'Developer'},
    {'email': '729488839@qq.com', 'role': 'Developer', 'site_access': 'all'},
]:
    st, b = probe('POST members body=%s' % list(body.keys()), 'POST',
                  '/api/v1/1643584176/members', body)
    if st in (200, 201, 202):
        print('  -> 邀请成功, 不再试其他形态')
        break
print()
print('== 2. 看 member 列表变化 ==')
st, b = probe('A GET members', 'GET', '/api/v1/1643584176/members')
print('done')
