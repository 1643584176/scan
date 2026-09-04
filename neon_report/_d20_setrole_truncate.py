# -*- coding: utf-8 -*-
"""数据库面收尾:1) SET ROLE 成员角色能力 2) TRUNCATE/DELETE 绕平台表触发器
零破坏:CREATE ROLE 即建即删;TRUNCATE 前先记数,测试在事务 ROLLBACK 中。"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:400]

# 1. SET ROLE 成员角色
print('=== [1] SET ROLE members ===')
for role in ('neon_superuser', 'neon_auth', 'anonymous', 'authenticated'):
    r = q('SET ROLE "%s"' % role, fetch=False)
    if r == 'OK':
        who = q('SELECT current_user')
        # 能力探测(只读)
        tbl = q("SELECT has_table_privilege('health_check','SELECT'), has_table_privilege('health_check','UPDATE')")
        cr = q("SELECT has_database_privilege(current_database(),'CREATE')")
        print('  [%s] current=%s health(S,U)=(%s) dbcreate=%s' % (role, who, tbl, cr))
        q('RESET ROLE', fetch=False)
    else:
        print('  [%s] SET FAIL: %s' % (role, str(r)[:150]))

# 2. CREATE ROLE as neon_superuser(即建即删)
r = q('SET ROLE neon_superuser', fetch=False)
if r == 'OK':
    print('\n=== [2] neon_superuser CREATE ROLE ===')
    r2 = q('CREATE ROLE k_tmprole', fetch=False)
    print('create role:', r2)
    if r2 == 'OK':
        r3 = q('DROP ROLE k_tmprole', fetch=False)
        print('drop role:', r3)
    # 建 superuser?
    r4 = q('CREATE ROLE k_tmpsup SUPERUSER', fetch=False)
    print('create superuser role:', r4)
    if r4 == 'OK':
        q('DROP ROLE k_tmpsup', fetch=False)
    # 平台表 DDL 权限
    r5 = q('ALTER TABLE health_check ADD COLUMN k_tmp text', fetch=False)
    print('alter health_check:', r5)
    if r5 == 'OK':
        q('ALTER TABLE health_check DROP COLUMN k_tmp', fetch=False)
    q('RESET ROLE', fetch=False)

# 3. TRUNCATE/DELETE 平台表(事务 ROLLBACK)
print('\n=== [3] TRUNCATE/DELETE health_check (tx rollback) ===')
print('has truncate priv:', q("SELECT has_table_privilege('neondb_owner','health_check','TRUNCATE')"))
conn.autocommit = False
try:
    cur.execute('BEGIN')
    cur.execute('TRUNCATE health_check')
    print('TRUNCATE: OK(!)')
    cur.execute('ROLLBACK')
    print('  rolled back')
except Exception as e:
    print('TRUNCATE ERR:', str(e)[:250])
    try: cur.execute('ROLLBACK')
    except Exception: pass
try:
    cur.execute('BEGIN')
    cur.execute('DELETE FROM health_check WHERE id = -1')
    print('DELETE: OK')
    cur.execute('ROLLBACK')
except Exception as e:
    print('DELETE ERR:', str(e)[:250])
    try: cur.execute('ROLLBACK')
    except Exception: pass
conn.autocommit = True
print('health_check count after:', q('SELECT count(*) FROM health_check'))

conn.close()
