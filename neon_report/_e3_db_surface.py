# -*- coding: utf-8 -*-
"""数据库残余面扫描(纯只读):pg_stat_statements 内容 / 大对象 / pg_cron 可用性 / 扩展清单
与 #3992341 主题隔离:无提权尝试,无写操作"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, args=None, fetch=True):
    try:
        cur.execute(sql, args or ())
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:300]

print('=== [1] pg_stat_statements 平台 SQL 内容(前 25 高频) ===')
print(q("""SELECT calls, queryid, left(query, 140) FROM pg_stat_statements
           ORDER BY calls DESC LIMIT 25"""))
print('\n--- 按最近(不按频率)---')
print(q("""SELECT calls, queryid, left(query, 140) FROM pg_stat_statements
           ORDER BY max_exec_time DESC NULLS LAST LIMIT 15"""))

print('\n=== [2] 大对象残留(owner 视角) ===')
print('metadata:', q("""SELECT pg_get_userbyid(lomowner) AS owner, count(*)
                        FROM pg_largeobject_metadata GROUP BY lomowner ORDER BY 2 DESC"""))
print('cloud_admin/neon_auth owner 大对象 oid:')
los = q("""SELECT oid FROM pg_largeobject_metadata
           WHERE lomowner IN (SELECT oid FROM pg_roles WHERE rolname IN ('cloud_admin','neon_auth','neon_superuser'))""")
print(los)

print('\n=== [3] pg_cron 可用性 ===')
print('available pg_cron:', q("""SELECT name, default_version, installed_version
                                 FROM pg_available_extensions WHERE name IN
                                 ('pg_cron','timescaledb','pg_partman','pg_repack','dblink','neon','neon_utils','neon_procstat','pg_session_jwt','plpgsql')
                                 ORDER BY name"""))
print('cron schema/函数存在?', q("""SELECT n.nspname, p.proname
                                     FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                                     WHERE p.proname IN ('schedule','unschedule','job_cache_invalidate')
                                     AND n.nspname='cron'"""))
print('扩展已安装清单:', q("""SELECT extname, extversion, pg_get_userbyid(extowner) FROM pg_extension ORDER BY 1"""))

print('\n=== [4] 其他 available 扩展(找平台特有/可疑) ===')
exts = q("""SELECT name, default_version FROM pg_available_extensions
            WHERE name NOT IN (SELECT extname FROM pg_extension)
            ORDER BY name""")
print('total available-not-installed:', len(exts) if isinstance(exts, list) else exts)
if isinstance(exts, list):
    print([e[0] for e in exts])

print('\n=== [5] 带密码角色确认(哪些可登录) ===')
print(q("""SELECT r.rolname, r.rolcanlogin, r.rolsuper,
                  (a.rolpassword IS NOT NULL) AS has_pw
           FROM pg_roles r LEFT JOIN pg_authid a ON a.oid = r.oid
           WHERE r.rolcanlogin ORDER BY r.rolname"""))

print('\n=== [6] 视图定义抽查(neon schema 统计视图的真实定义) ===')
print(q("""SELECT viewname, left(definition, 200) FROM pg_views
           WHERE schemaname='neon' LIMIT 3"""))
print(q("""SELECT viewname, left(definition, 300) FROM pg_views
           WHERE schemaname='public' AND viewname='pg_stat_statements'"""))

print('\n=== [7] 有无 cron/调度相关表被隐藏(全 schema 函数 owner 高权扫描) ===')
print(q("""SELECT n.nspname, p.proname, pg_get_userbyid(p.proowner) AS owner, p.prosecdef
           FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
           WHERE p.prosecdef AND n.nspname NOT IN ('pg_catalog','information_schema')
             AND pg_get_userbyid(p.proowner) IN ('cloud_admin','neon_superuser','neon_auth','postgres')
           LIMIT 20"""))

conn.close()
