# -*- coding: utf-8 -*-
"""T1b: 直连 postgres 库(neondb_owner)列全部可见对象, 对比 schema 导出对象集, 找导出独有对象"""
import psycopg, json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

URI = 'postgresql://neondb_owner:npg_P0niS8eNFkjT@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/postgres?sslmode=require'
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()

# 1) 表/视图/物化视图 (非系统 schema)
cur.execute("""
    SELECT n.nspname, c.relname, c.relkind
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
      AND c.relkind IN ('r','v','m','f','p','S')
    ORDER BY n.nspname, c.relname
""")
tables = cur.fetchall()
print('== 直连可见 表/视图/序列: %d' % len(tables))
for nsp, rel, kind in tables:
    print('   %s.%s (%s)' % (nsp, rel, kind))

# 2) 函数 (名字 + 是否可读 prosrc)
cur.execute("""
    SELECT n.nspname, p.proname, pg_get_function_identity_arguments(p.oid),
           pg_get_functiondef(p.oid) IS NOT NULL AS def_visible
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY n.nspname, p.proname
""")
funcs = cur.fetchall()
print('\n== 直连可见 函数: %d' % len(funcs))
for nsp, pn, args, dv in funcs:
    print('   %s.%s(%s) def_visible=%s' % (nsp, pn, args[:60], dv))

# 3) schema 导出中的对象名集合 (从 SQL 提取)
sql = open(r'D:\scan\neon_report\_nz44_schema_postgres.sql', encoding='utf-8').read()
exported = set(re.findall(r'CREATE (?:TABLE|VIEW|FUNCTION|SCHEMA|EXTENSION|TRIGGER)\s+(?:IF NOT EXISTS\s+)?(?:public\.)?([\w.]+)', sql))
print('\n== 导出对象名: %s' % sorted(exported))

visible = set(nsp + '.' + rel for nsp, rel, _ in tables) | set(nsp + '.' + pn for nsp, pn, _, _ in funcs)
# 规范化比较: 导出名可能是 public.xxx 或无 schema 前缀
print('\n== 对比结论 ==')
for e in sorted(exported):
    name = e.split('.')[-1] if '.' in e else e
    hit = any(name == v.split('.')[-1] and ('.' not in v or v.split('.')[0] in ('public', nsp0)) for v in visible for nsp0 in ['public'])
    print('   %-40s 直连可见=%s' % (e, any(name == v.split('.')[-1] for v in visible)))

conn.close()
