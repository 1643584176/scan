# -*- coding: utf-8 -*-
"""深挖 /api/authed_users/plans:B cookie 返回 A 的 plan?
核心问题:响应里的 A 数据是因为 cookie 含 A token,还是后端越权?
测试:1.完整响应 2.纯B cookie(authn 删 A token) 3.匿名
"""
import json, sys, http.client, ssl, gzip, brotli, urllib.parse
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, UID_A, UID_B, TEAM_A, TEAM_B

HOST = 'www.figma.com'

def req(method, path, body=None, ct='application/json', cookie=None, extra=None):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
    hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
            'Accept-Encoding': 'br, gzip'}
    if cookie:
        hdrs['Cookie'] = cookie
    if body is not None:
        hdrs['Content-Type'] = ct
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        hdrs['Content-Length'] = str(len(body))
    if extra:
        hdrs.update(extra)
    conn.request(method, path, body=body, headers=hdrs)
    resp = conn.getresponse()
    raw = resp.read()
    enc = resp.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    conn.close()
    return resp.status, raw.decode('utf-8', 'ignore')

# 构造"纯B" cookie:从 authn JSON 中删除 A 的条目,并相应处理 embed/user_prefs
def make_pure_b():
    pairs = COOKIE_B.split('; ')
    out = []
    for p in pairs:
        k, _, v = p.partition('=')
        if k == '__Host-figma.authn':
            try:
                j = json.loads(urllib.parse.unquote(v))
                j.pop(UID_A, None)
                out.append(k + '=' + urllib.parse.quote(json.dumps(j)))
            except Exception:
                out.append(p)
        elif k == '__Host-figma.embed':
            try:
                j = json.loads(urllib.parse.unquote(v))
                j.pop(UID_A, None)
                out.append(k + '=' + urllib.parse.quote(json.dumps(j)))
            except Exception:
                out.append(p)
        elif k == '__Host-figma.user_prefs':
            # 保留(可能含 A 条目,暂不动)
            out.append(p)
        else:
            out.append(p)
    return '; '.join(out)

PURE_B = make_pure_b()
print('pureB 构造完成, authn 剩余 uid 数(应为1):')
for p in PURE_B.split('; '):
    if p.startswith('__Host-figma.authn='):
        print('   authn:', urllib.parse.unquote(p.split('=', 1)[1])[:120])

for label, ck in [('B cookie(原)', COOKIE_B), ('纯B cookie(删A token)', PURE_B), ('匿名', None)]:
    s, txt = req('GET', '/api/authed_users/plans', cookie=ck)
    print()
    print('[%s] %d' % (label, s))
    print('   ', txt[:900].replace('\n', ' '))
