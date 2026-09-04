# -*- coding: utf-8 -*-
"""③ diff 结构理解:在 agent 分支建 k_ 测试表 -> diff 看差异结构 -> 清理
database-query(B cookie + branchId=agent1)写 agent 分支库
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
BR_A1 = 'agent-6a98d5e6448c07a76d7babf3'
ctx = ssl.create_default_context()


def dbq(body, timeout=45):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_B}
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


def q(label, sql, branch='production'):
    st, out = dbq({'siteId': SITE_B, 'branchId': branch, 'action': 'query', 'sql': sql})
    print('%-40s [%d] %s' % (label, st, out.replace('\n', ' | ')[:300]))


def api(method, path, body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + TOKEN_B}
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    out = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, out


from _net_creds import TOKEN_B
base = '/api/v1/sites/%s/database/branch' % SITE_B

print('== agent1 分支基线 ==')
q('agent1 建测试表', 'create table if not exists k_diff_t1(id int primary key, name text)', BR_A1)
q('agent1 确认', "select to_regclass('public.k_diff_t1')::text", BR_A1)
print()
print('== diff agent1(应含差异)==')
st, out = api('POST', '%s/%s/diff' % (base, BR_A1))
print('[%d] %s' % (st, out[:1500]))
print()
print('== diff production(对照)==')
st, out = api('POST', '%s/production/diff' % (base,))
print('[%d] %s' % (st, out[:800]))
print()
print('== 清理 agent1 ==')
q('agent1 drop 测试表', 'drop table if exists k_diff_t1', BR_A1)
q('agent1 确认清理', "select to_regclass('public.k_diff_t1')::text", BR_A1)
