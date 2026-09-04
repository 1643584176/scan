# -*- coding: utf-8 -*-
"""事件触发器定论:同事务分步执行(不 fetch 多语句)"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def tx(steps):
    """steps: [(label, sql)] 同一事务内顺序执行, 最后 ROLLBACK"""
    out = []
    try:
        cur.execute('BEGIN')
    except Exception:
        pass
    for label, sql in steps:
        try:
            cur.execute(sql)
            out.append('%s: OK' % label)
        except Exception as e:
            out.append('%s: ERR %s' % (label, str(e)[:200]))
    try:
        cur.execute('ROLLBACK')
    except Exception:
        pass
    return out

print('=== [1] 同事务 CREATE FUNCTION + EVENT TRIGGER ===')
for r in tx([('create fn', "CREATE FUNCTION k_evt() RETURNS event_trigger AS 'BEGIN NULL; END' LANGUAGE plpgsql"),
             ('create evt', "CREATE EVENT TRIGGER k_evt_trg ON ddl_command_end EXECUTE FUNCTION k_evt()")]):
    print(' ', r)

print('\n=== [2] 同上 + SET neon.event_triggers=on ===')
for r in tx([('set guc', "SET neon.event_triggers='on'"),
             ('create fn', "CREATE FUNCTION k_evt2() RETURNS event_trigger AS 'BEGIN NULL; END' LANGUAGE plpgsql"),
             ('create evt', "CREATE EVENT TRIGGER k_evt2_trg ON sql_drop EXECUTE FUNCTION k_evt2()")]):
    print(' ', r)

print('\n=== [3] 只 CREATE EVENT TRIGGER 引用已存在函数不可行,改为验证 PG 原生要求:直接试 ===')
print('(CREATE EVENT TRIGGER 需要 superuser 是 PG 原生规则,以上两测若报 permission denied 即定论)')

conn.close()
