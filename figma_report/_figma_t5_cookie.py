# -*- coding: utf-8 -*-
"""t5: Cookie 畸形/同名 cookie 解析差异
1. authn JSON 键序对调(A在前/B在前)→ livegraph authSuccess 身份?
2. 双同名 authn cookie → 后端取哪个?
3. 畸形 authn(截断/空)→ fallback 行为?
身份判定端点:GET /api/authed_users/plans(plans_by_user_id 的 uid 集合)
"""
import json, sys, http.client, ssl, gzip, brotli, urllib.parse, time, websocket
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, UID_A, UID_B, FILE_A

HOST = 'www.figma.com'
ORIGIN = 'https://www.figma.com'

# ---- 工具:解析/重排 cookie ----
def get_authn():
    for p in COOKIE_B.split('; '):
        if p.startswith('__Host-figma.authn='):
            return p.split('=', 1)[1]
    return None

def swap_authn_order():
    """把 authn JSON 键序对调(B在前 -> A在前)"""
    v = get_authn()
    j = json.loads(urllib.parse.unquote(v))
    keys = list(j.keys())
    rev = {k: j[k] for k in reversed(keys)}
    return urllib.parse.quote(json.dumps(rev))

def rebuild_cookie(new_authn=None, extra_authn=None, truncate_authn=False):
    """重建 cookie 串"""
    pairs = []
    for p in COOKIE_B.split('; '):
        k = p.split('=', 1)[0]
        if k == '__Host-figma.authn' and new_authn is not None:
            if truncate_authn:
                pairs.append('__Host-figma.authn=' + new_authn[:30])
            else:
                pairs.append('__Host-figma.authn=' + new_authn)
            if extra_authn is not None:
                pairs.append('__Host-figma.authn=' + extra_authn)
        else:
            pairs.append(p)
    return '; '.join(pairs)

def req_plans(cookie):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
    hdrs = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip',
            'Origin': ORIGIN, 'Referer': ORIGIN + '/'}
    if cookie:
        hdrs['Cookie'] = cookie
    conn.request('GET', '/api/authed_users/plans', headers=hdrs)
    resp = conn.getresponse()
    raw = resp.read()
    enc = resp.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    conn.close()
    return resp.status, raw.decode('utf-8', 'ignore')

def uid_set(txt):
    try:
        m = json.loads(txt).get('meta', {}).get('plans_by_user_id', {})
        return set(m.keys())
    except Exception:
        return '?'

AUTHN_ORIG = get_authn()
AUTHN_SWAP = swap_authn_order()
print('authn 原始:', urllib.parse.unquote(AUTHN_ORIG)[:100])
print('authn 对调:', urllib.parse.unquote(AUTHN_SWAP)[:100])

cases = [
    ('原cookie(A,B顺序)', COOKIE_B),
    ('authn键序对调(B在前)', rebuild_cookie(AUTHN_SWAP)),
    ('双同名authn(原+对调)', rebuild_cookie(AUTHN_ORIG, AUTHN_SWAP)),
    ('双同名authn(对调+原)', rebuild_cookie(AUTHN_SWAP, AUTHN_ORIG)),
    ('authn截断30字符', rebuild_cookie(AUTHN_ORIG, truncate_authn=True)),
    ('authn空JSON', rebuild_cookie(urllib.parse.quote('{}'))),
    ('authn非法JSON', rebuild_cookie('abc')),
]
for label, ck in cases:
    s, txt = req_plans(ck)
    print('[%s] %d uid_set=%s' % (label, s, uid_set(txt)))
