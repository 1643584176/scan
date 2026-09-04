# -*- coding: utf-8 -*-
"""第四轮:pg_authid 可读权限根因定位(外部 psycopg 多语句单连接)
R1 目录 owner/relacl/initprivs 细查
R2 SET ROLE 矩阵:哪个成员角色赋予 pg_authid 读权限
R3 readonly 角色对照(无 pg_* 成员 -> 预期不可读)
R4 neon_service 角色能力盘点
R5 顺带:pg_shadow 视图 ACL、其他敏感目录可读性
"""
import sys, psycopg
sys.path.insert(0, r'D:\scan\netlify_report')

EP_A = 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com'
PW_OWN = 'npg_MtTpnyk2LE4j'
PW_RO = 'WCtJ-h-b7w82YMIaM598M75SV7uYVTCv'


def run(user, pw, statements, db='netlifydb', tag=''):
    """多语句单连接执行,返回每段结果/错误"""
    try:
        with psycopg.connect(host=EP_A, port=5432, dbname=db, user=user, password=pw,
                             sslmode='require', connect_timeout=15, autocommit=True) as c:
            with c.cursor() as cur:
                out = []
                for s in statements:
                    try:
                        cur.execute(s)
                        if cur.description:
                            rows = cur.fetchall()
                            out.append((s[:60], 'ROWS', str(rows)[:400]))
                        else:
                            out.append((s[:60], 'OK', cur.statusmessage or ''))
                    except Exception as e:
                        out.append((s[:60], 'ERR', str(e)[:300]))
                        try:
                            c.rollback()
                        except Exception:
                            pass
        return out
    except Exception as e:
        return [('CONNECT', 'ERR', str(e)[:300])]


def pr(prefix, rows):
    for s, kind, msg in rows:
        print('%-28s [%s] %s' % (prefix + s, kind, msg.replace('\n', ' ')[:380]))
    print()


print('========== R1. pg_authid 目录 owner/relacl/initprivs ==========')
pr('A owner | ', run('netlifydb_owner', PW_OWN, [
    "select relname, relowner::regrole::text, relacl::text from pg_class "
    "where relname in ('pg_authid','pg_shadow','pg_database','pg_auth_members','pg_user_mapping') order by 1",
    "select objoid::regclass::text, privtype, array_to_string(initprivs, ',') as grants "
    "from pg_init_privs where classoid = 'pg_class'::regclass and "
    "array_to_string(initprivs, ',') like '%pg_read_all_data%' or array_to_string(initprivs, ',') like '%pg_write_all_data%' "
    "or array_to_string(initprivs, ',') like '%neon_superuser%'",
]))

print('========== R2. SET ROLE 矩阵(owner 单连接内逐角色) ==========')
for role in ('pg_read_all_data', 'pg_write_all_data', 'pg_monitor', 'pg_read_all_stats',
             'pg_stat_scan_tables', 'pg_maintain', 'neon_superuser'):
    pr('%s | ' % role, run('netlifydb_owner', PW_OWN, [
        'set role %s' % role,
        'select count(*) as n from pg_authid',
        "select rolname from pg_shadow",
        'reset role',
    ]))

print('========== R3. readonly 角色对照 ==========')
pr('readonly | ', run('netlifydb_readonly', PW_RO, [
    "select current_user, (select string_agg(rolname, ',') from pg_roles where pg_has_role(current_user, oid, 'member'))",
    'select count(*) as n from pg_authid',
    "select rolname from pg_shadow",
]))

print('========== R4. neon_service 角色能力 ==========')
pr('A owner | ', run('netlifydb_owner', PW_OWN, [
    "select rolname, rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, rolreplication, rolcanlogin "
    "from pg_roles where rolname = 'neon_service'",
    "select r.rolname as member_of from pg_auth_members m join pg_roles r on r.oid = m.roleid "
    "where m.member = 'neon_service'::regrole",
    "select c.relname, c.relacl::text from pg_class c where c.relacl is not null "
    "and c.relacl::text like '%neon_service%' limit 20",
    "select p.proname, p.proacl::text from pg_proc p where p.proacl is not null "
    "and p.proacl::text like '%neon_service%' limit 20",
]))

print('========== R5. 其他敏感对象可读性 ==========')
pr('A owner | ', run('netlifydb_owner', PW_OWN, [
    "select count(*) from pg_auth_members",
    "select count(*) from pg_db_role_setting",
    "select count(*) from pg_replication_slots",
    "select count(*) from pg_largeobject",
    "select count(*) from pg_subscription",
    "select count(*) from pg_publication",
    "select count(*) from pg_statistic",
    "select count(*) from pg_replslot",
]))
