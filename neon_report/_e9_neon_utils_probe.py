# -*- coding: utf-8 -*-
"""neon_utils 1.1 函数面审计(事务内,ROLLBACK 零残留)
Neon 自家平台扩展可被租户安装 -> 枚举全部函数/描述/属主/ACL,找平台信息泄露面"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

print('=== neon_utils 安装(事务内) ===')
cur.execute('BEGIN')
try:
    cur.execute('CREATE EXTENSION neon_utils')
    print('installed OK')
except Exception as e:
    print('install ERR:', str(e)[:200])
    conn.rollback()
    conn.close()
    raise SystemExit

print('\n=== [1] 全部函数 ===')
cur.execute("""SELECT p.proname, pg_get_function_identity_arguments(p.oid) AS args,
                      pg_get_userbyid(p.proowner) AS owner, p.prosecdef, p.provolatile,
                      COALESCE(obj_description(p.oid), '') AS descr
               FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
               WHERE n.nspname='public'
               ORDER BY p.proname""")
funcs = cur.fetchall()
for f in funcs:
    print('%-45s %-40s owner=%-14s def=%s vol=%s | %s' % (f[0], f[1][:38], f[2], f[3], f[4], f[5][:80]))

print('\n=== [2] 属主非 neondb_owner 的对象(cloud_admin 上下文创建) ===')
cur.execute("""SELECT c.relname, c.relkind, pg_get_userbyid(c.relowner)
               FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='public' AND pg_get_userbyid(c.relowner) <> 'neondb_owner'""")
print(cur.fetchall())

print('\n=== [3] SECURITY DEFINER / volatile 函数尝试调用(只读语义) ===')
for f in funcs:
    if f[2] == 'cloud_admin' or f[3]:
        fn = f[0]
        # 只尝试无参或可空参调用——先看签名,避免副作用
        print('  candidate:', fn, '(', f[1], ') def=%s' % f[3])

print('\n=== [4] 函数依赖扩展注释(找平台用途线索) ===')
cur.execute("""SELECT p.proname, d.description FROM pg_proc p
               JOIN pg_namespace n ON n.oid=p.pronamespace
               LEFT JOIN pg_description d ON d.objoid=p.oid
               WHERE n.nspname='public' AND d.description IS NOT NULL
               ORDER BY p.proname LIMIT 10""")
for r in cur.fetchall():
    print(' ', r)

conn.rollback()
print('\nrolled back; 残留:', end=' ')
cur.execute("SELECT extname FROM pg_extension WHERE extname='neon_utils'")
print(cur.fetchall())
conn.close()
