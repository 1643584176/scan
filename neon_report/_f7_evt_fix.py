# -*- coding: utf-8 -*-
"""补测:同事务 CREATE FUNCTION + CREATE EVENT TRIGGER(定论权限)
+ deprecated/unstable 扩展列表值 + SCRAM 字典准备"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def step(tag, sql=None, fetch=True):
    if sql is None:
        sql = tag
    try:
        cur.execute('BEGIN')
    except Exception:
        pass
    try:
        cur.execute(sql)
        r = cur.fetchall() if fetch else 'OK'
        cur.execute('ROLLBACK')
        return r
    except Exception as e:
        try:
            cur.execute('ROLLBACK')
        except Exception:
            pass
        return 'ERR: %s' % str(e)[:250]

print('=== [1] 同事务 CREATE FUNCTION + EVENT TRIGGER(定论) ===')
print(step("""CREATE FUNCTION k_evt() RETURNS event_trigger AS 'BEGIN NULL; END' LANGUAGE plpgsql;
              CREATE EVENT TRIGGER k_evt_trg ON ddl_command_end EXECUTE FUNCTION k_evt()"""))
print(step("""SET neon.event_triggers='on';
              CREATE FUNCTION k_evt3() RETURNS event_trigger AS 'BEGIN NULL; END' LANGUAGE plpgsql;
              CREATE EVENT TRIGGER k_evt3_trg ON sql_drop EXECUTE FUNCTION k_evt3()"""))

print('\n=== [2] deprecated/unstable 列表值 ===')
print('deprecated:', step("SELECT setting FROM pg_settings WHERE name='neon.deprecated_extensions'"))
print('unstable:', step("SELECT setting FROM pg_settings WHERE name='neon.unstable_extensions'"))
print('allow_unstable:', step("SELECT setting FROM pg_settings WHERE name='neon.allow_unstable_extensions'"))

print('\n=== [3] 事件触发器现状(平台自己有没有用) ===')
print(step("SELECT evtname, evtevent, pg_get_userbyid(evtowner) FROM pg_event_trigger"))

print('\n=== [4] 规则/触发器面现状复核(neondb 库,平台相关对象) ===')
print(step("""SELECT c.relname, pg_get_userbyid(c.relowner), count(t.oid)
              FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
              WHERE NOT t.tgisinternal GROUP BY 1,2 LIMIT 20"""))

print('\n=== [5] extension_server 相关(neon.extension_server_port=postmaster 但值?) ===')
print(step("SELECT name, setting FROM pg_settings WHERE name IN ('neon.extension_server_port','neon.extension_server_connect_timeout','neon.extension_server_request_timeout','neon.forward_ddl','neon.privileged_role_name','neon.restrict_superuser_calls','neon.membership_roles_filter','neon.project_id','neon.tenant_id','neon.endpoint_id','neon.timeline_id')"))

conn.close()
