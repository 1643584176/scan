# -*- coding: utf-8 -*-
"""③ apply 收尾:分支落后于 production 场景(apply 可能同步 DDL 到分支)
观察:diff 形态 -> apply 是否执行 -> 执行后 agent1 结构/owner
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
        st, out = r.status, raw[:500].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'EXC %r' % e
    finally:
        conn.close()
    return st, out


def q(label, sql, branch='production'):
    st, out = dbq({'siteId': SITE_B, 'branchId': branch, 'action': 'query', 'sql': sql})
    print('%-44s [%d] %s' % (label, st, out.replace('\n', ' | ')[:240]))
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
print('== 构造:production 领先(id,name),agent1 落后(id)==')
q('production 建表', 'create table if not exists k_diff_t1(id int primary key, name text)')
q('agent1 建表(少列)', 'create table if not exists k_diff_t1(id int primary key)', BR_A1)
print()
print('== diff agent1 ==')
st, out = api('POST', '%s/%s/diff' % (base, BR_A1))
print('[%d] %s' % (st, out[:800]))
print()
print('== apply 该表 ==')
st, out = api('POST', '%s/%s/apply' % (base, BR_A1), {'tables': [{'schema': 'public', 'name': 'k_diff_t1'}]})
print('[%d] %s' % (st, out[:500]))
print()
print('== agent1 是否被同步 ==')
q('agent1 列', "select string_agg(column_name, ',') from information_schema.columns where table_name='k_diff_t1'", BR_A1)
q('agent1 owner', "select tableowner from pg_tables where tablename='k_diff_t1'", BR_A1)
print()
print('== 清理 ==')
q('production drop', 'drop table if exists k_diff_t1')
q('agent1 drop', 'drop table if exists k_diff_t1', BR_A1)
q('确认 production', "select to_regclass('public.k_diff_t1')::text")
q('确认 agent1', "select to_regclass('public.k_diff_t1')::text", BR_A1)
