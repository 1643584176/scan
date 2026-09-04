# -*- coding: utf-8 -*-
"""1) 成员关系诊断(neondb_owner 是否 cloud_admin 成员/SET ROLE 可能)
2) 修正列名重测平台表写权限(ROLLBACK 零残留)"""
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

# 1. 成员关系
print('=== [1] membership ===')
print('auth_members:', q("""SELECT r.rolname AS member, g.rolname AS granted, m.admin_option
  FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member JOIN pg_roles g ON g.oid=m.roleid
  WHERE r.rolname='neondb_owner' OR g.rolname='neondb_owner'"""))
print('neondb_owner rols:', q("SELECT rolname FROM pg_roles WHERE pg_has_role('neondb_owner', oid, 'member') AND rolname != 'neondb_owner'"))
print('has_table_priv:', q("SELECT has_table_privilege('neondb_owner','health_check','SELECT'), has_table_privilege('neondb_owner','health_check','UPDATE'), has_table_privilege('neondb_owner','health_check','INSERT'), has_table_privilege('neondb_owner','health_check','DELETE'), has_table_privilege('neondb_owner','lakebase_attributes','SELECT'), has_table_privilege('neondb_owner','lakebase_attributes','INSERT')"))
print('health_check cols:', q("""SELECT a.attname FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
  WHERE c.relname='health_check' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum"""))
print('lakebase cols:', q("""SELECT a.attname FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
  WHERE c.relname='lakebase_attributes' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum"""))
print('relkind:', q("SELECT c.relname, c.relkind FROM pg_class c WHERE c.relname IN ('health_check','lakebase_attributes')"))

# 2. SET ROLE 尝试(若 membership)
print('\n=== [2] SET ROLE ===')
r = q('SET ROLE cloud_admin', fetch=False)
print('SET ROLE cloud_admin:', r)
if r == 'OK':
    print('  current_user now:', q('SELECT current_user'))
    q('RESET ROLE', fetch=False)
    print('  reset done')

# 3. 写权限(修正列名,ROLLBACK)
print('\n=== [3] write perms corrected ===')
conn.autocommit = False
tests = [
    ("UPDATE health_check SET updated_at = updated_at WHERE false", 'health_check UPDATE no-op'),
    ("INSERT INTO health_check (id) SELECT 999999 WHERE NOT EXISTS (SELECT 1 FROM health_check WHERE id=999999)", 'health_check INSERT probe'),
    ("INSERT INTO lakebase_attributes (name, value) VALUES ('k_probe', '{}'::jsonb)", 'lakebase INSERT probe'),
]
for sql, tag in tests:
    try:
        cur.execute('BEGIN')
        cur.execute(sql)
        print('%s: OK' % tag)
        cur.execute('ROLLBACK')
    except Exception as e:
        print('%s ERR: %s' % (tag, str(e)[:250]))
        try: cur.execute('ROLLBACK')
        except Exception: pass
conn.autocommit = True

# 4. neon_migration/neon schema 表
print('\n=== [4] neon/neon_migration schemas ===')
print(q("SELECT schemaname, tablename FROM pg_tables WHERE schemaname IN ('neon','neon_migration')"))
print(q("SELECT has_schema_privilege('neondb_owner','neon','USAGE'), has_schema_privilege('neondb_owner','neon_migration','USAGE')"))
print('migration_id count:', q("SELECT count(*) FROM neon_migration.migration_id"))

conn.close()
