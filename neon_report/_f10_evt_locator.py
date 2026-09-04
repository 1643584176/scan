# -*- coding: utf-8 -*-
"""事件触发器触发场景定位(续):
A) console API CREATE DATABASE -> 观察 neondb 触发器
B) postgres 库建探测触发器可行性(CREATE FUNCTION/EVENT TRIGGER 权限)
零破坏:任何触发都只写 neondb.k_evt_log;postgres 库对象用完即删"""
import psycopg, json, urllib.request, time, random

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI_ND = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
URI_PG = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)

conn_nd = psycopg.connect(URI_ND, connect_timeout=20)
conn_nd.autocommit = True
cur_nd = conn_nd.cursor()

def q(cur, sql):
    try:
        cur.execute(sql)
        try:
            return cur.fetchall()
        except Exception:
            return 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:250]

cfg = json.load(open(r'D:\scan\neon_report\_apikey.json'))
API_HOST = 'console-stage.neon.build'
API_BASE = '/api/v2'
KEY = cfg.get('key') or cfg.get('api_key') or ''
PROJ = 'orange-sun-90493739'
BID = 'br-wandering-field-w2ob6mpn'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

def api(path, method='GET', body=None):
    url = 'https://%s%s%s' % (API_HOST, API_BASE, path)
    req = urllib.request.Request(url, method=method)
    req.add_header('Authorization', 'Bearer %s' % KEY)
    req.add_header('X-Bug-Bounty', 'xxbo')
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', UA)
    req.add_header('Accept', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=25) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]
    except Exception as e:
        return 0, str(e)[:300]

print('=== [A1] console CREATE DATABASE(触发 neondb DDL?) ===')
dbn = 'k_evt_db_%d' % random.randint(100000, 999999)
st, r = api('/projects/%s/branches/%s/databases' % (PROJ, BID), 'POST', {'database': {'name': dbn, 'owner_name': 'neondb_owner'}})
print('create db:', st, str(r)[:300])
time.sleep(3)
print('neondb evt log:', q(cur_nd, 'SELECT * FROM public.k_evt_log ORDER BY t'))
# 清理数据库
if st == 201 or (isinstance(r, dict) and r.get('database')):
    st2, r2 = api('/projects/%s/branches/%s/databases/%s' % (PROJ, BID, dbn), 'DELETE')
    print('cleanup db:', st2, str(r2)[:200])
else:
    # 403 可能是 owner_name 问题,试默认
    st3, r3 = api('/projects/%s/branches/%s/databases' % (PROJ, BID), 'POST', {'database': {'name': dbn}})
    print('retry create db:', st3, str(r3)[:300])
    time.sleep(3)
    print('neondb evt log after retry:', q(cur_nd, 'SELECT * FROM public.k_evt_log ORDER BY t'))
    if st3 == 201 or (isinstance(r3, dict) and r3.get('database')):
        api('/projects/%s/branches/%s/databases/%s' % (PROJ, BID, dbn), 'DELETE')

print('\n=== [A2] 等待几秒看延迟触发 ===')
time.sleep(5)
print('neondb evt log final:', q(cur_nd, 'SELECT * FROM public.k_evt_log ORDER BY t'))

print('\n=== [B] postgres 库建探测触发器可行性 ===')
conn_pg = psycopg.connect(URI_PG, connect_timeout=20)
conn_pg.autocommit = True
cur_pg = conn_pg.cursor()
print('pg: CREATE FUNCTION:', q(cur_pg, "CREATE OR REPLACE FUNCTION public.k_evt_probe_pg() RETURNS event_trigger AS 'BEGIN NULL; END' LANGUAGE plpgsql"))
print('pg: CREATE EVENT TRIGGER:', q(cur_pg, 'DROP EVENT TRIGGER IF EXISTS k_evt_probe_pg_trg'))
print(q(cur_pg, 'CREATE EVENT TRIGGER k_evt_probe_pg_trg ON ddl_command_end EXECUTE FUNCTION public.k_evt_probe_pg()'))
print('pg: existing evt trgs:', q(cur_pg, 'SELECT evtname FROM pg_event_trigger'))
# 清理
print('pg cleanup:', q(cur_pg, 'DROP EVENT TRIGGER IF EXISTS k_evt_probe_pg_trg'))
print(q(cur_pg, 'DROP FUNCTION IF EXISTS public.k_evt_probe_pg()'))
conn_pg.close()

print('\n=== [C] 若 B 成功(建了又删):用 dblink 型函数重试在 postgres 库 ===')
conn_nd.close()
