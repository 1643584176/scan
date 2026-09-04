# -*- coding: utf-8 -*-
"""收尾快测:1)auth GUC 注入状态与伪造可达性 2)lakebase DELETE/约束 3)postgres 库 public CREATE 权限(全零破坏)"""
import psycopg

# --- neondb:auth GUC 状态 ---
URI1 = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI1, connect_timeout=15)
conn.autocommit = True
cur = conn.cursor()

def q1(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

print('=== [1] jwk GUC 注入状态(直连) ===')
print(q1("SELECT current_setting('pg_session_jwt.jwk', true)"))
print('=== [2] auth.uid() 当前 ===')
print(q1("SELECT auth.uid()"))
print('=== [3] SET request.jwt.claims 后 auth.uid()(Userset GUC) ===')
try:
    cur.execute("SET request.jwt.claims = '{\"sub\": \"00000000-0000-0000-0000-000000000001\", \"role\": \"authenticated\"}'")
    print(q1("SELECT auth.uid(), auth.session()"))
except Exception as e:
    print('ERR:', str(e)[:200])
conn.close()

# --- postgres:lakebase DELETE + CREATE 权限 ---
URI2 = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/postgres'
conn2 = psycopg.connect(URI2, connect_timeout=15)
conn2.autocommit = True
cur2 = conn2.cursor()

def q2(sql):
    try:
        cur2.execute(sql)
        return cur2.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

print('=== [4] lakebase DELETE 权限(0 行条件) ===')
print(q2("DELETE FROM lakebase_attributes WHERE name = '__k_noexist__'"))
print('=== [5] postgres 库 public CREATE TABLE 权限 ===')
try:
    cur2.execute("CREATE TABLE k_probe_t (id int)")
    print('  CREATE OK(将删除)')
    cur2.execute("DROP TABLE k_probe_t")
    print('  dropped')
except Exception as e:
    print('  CREATE DENIED:', str(e)[:150])
print('=== [6] lakebase 表约束(有无 CHECK/唯一限制 name 值域) ===')
print(q2("""SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
  WHERE conrelid='lakebase_attributes'::regclass"""))
conn2.close()
