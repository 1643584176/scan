# -*- coding: utf-8 -*-
"""③ apply 桥:构造 production/agent1 兼容差异 -> 探合法 body -> 观察执行后对象 owner
若 apply 执行 DDL 后表 owner != netlifydb_owner -> 高权限通道证据
全程 k_ 表,结束清理
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B, TOKEN_B

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
        st, out = r.status, raw[:600].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'EXC %r' % e
    finally:
        conn.close()
    return st, out


def q(label, sql, branch='production'):
    st, out = dbq({'siteId': SITE_B, 'branchId': branch, 'action': 'query', 'sql': sql})
    print('%-42s [%d] %s' % (label, st, out.replace('\n', ' | ')[:280]))
    return st, out


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


base = '/api/v1/sites/%s/database/branch' % SITE_B
print('== 构造:两分支都有 k_diff_t1,结构不同 ==')
q('production 建表(id)', 'create table if not exists k_diff_t1(id int primary key)')
q('agent1 建表(id,name)', 'create table if not exists k_diff_t1(id int primary key, name text)', BR_A1)
print()
print('== diff agent1(结构差异)==')
st, out = api('POST', '%s/%s/diff' % (base, BR_A1))
print('[%d] %s' % (st, out[:1200]))
print()
print('== apply body 变体探测(先不真执行:全用 k_noexist_ 表)==')
bodies = [
    {'tables': ['k_noexist_xyz']},
    {'tables': [{'name': 'k_noexist_xyz'}]},
    {'tables': [{'schema': 'public', 'name': 'k_noexist_xyz'}]},
    {'tables': [{'schema': 'public', 'name': 'k_diff_t1'}]},
]
for b in bodies:
    st, out = api('POST', '%s/%s/apply' % (base, BR_A1), b)
    print('%-70s [%d] %s' % (str(b)[:68], st, out[:220]))
print()
print('== 清理 ==')
q('production drop', 'drop table if exists k_diff_t1')
q('agent1 drop', 'drop table if exists k_diff_t1', BR_A1)
q('确认 production', "select to_regclass('public.k_diff_t1')::text")
q('确认 agent1', "select to_regclass('public.k_diff_t1')::text", BR_A1)
