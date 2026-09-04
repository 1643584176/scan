# -*- coding: utf-8 -*-
"""③ apply 一致场景:确认 apply 是否有 DDL 执行能力 / dry_run 语义
两边表一致 -> diff 应无差异 -> apply 合法 body -> 观察响应与库变化
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
print('== 构造:两分支一致的 k_diff_t1 ==')
q('production 建表', 'create table if not exists k_diff_t1(id int primary key, name text)')
q('agent1 建表(相同结构)', 'create table if not exists k_diff_t1(id int primary key, name text)', BR_A1)
print()
print('== diff agent1(应无差异)==')
st, out = api('POST', '%s/%s/diff' % (base, BR_A1))
print('[%d] %s' % (st, out[:800]))
print()
print('== apply: 一致表 + dry_run ==')
tb = {'schema': 'public', 'name': 'k_diff_t1'}
for body in [{'tables': [tb], 'dry_run': True}, {'tables': [tb]}, {'tables': [tb], 'dry_run': False}]:
    st, out = api('POST', '%s/%s/apply' % (base, BR_A1), body)
    print('%-58s [%d] %s' % (str(body)[:56], st, out[:400]))
print()
print('== 库状态对比(apply 是否改了什么)==')
q('production 列', "select string_agg(column_name, ',') from information_schema.columns where table_name='k_diff_t1'")
q('agent1 列', "select string_agg(column_name, ',') from information_schema.columns where table_name='k_diff_t1'", BR_A1)
q('production owner', "select tableowner from pg_tables where tablename='k_diff_t1'")
q('agent1 owner', "select tableowner from pg_tables where tablename='k_diff_t1'", BR_A1)
print()
print('== 清理 ==')
q('production drop', 'drop table if exists k_diff_t1')
q('agent1 drop', 'drop table if exists k_diff_t1', BR_A1)
