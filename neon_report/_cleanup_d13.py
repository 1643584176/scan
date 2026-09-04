# -*- coding: utf-8 -*-
"""清理 _d13 残留:比对 _neonauth_priv.txt(官方私钥)区分 jwks 行,删测试行 + demo_rls"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
official = open(r'D:\scan\neon_report\_neonauth_priv.txt', encoding='utf-8').read().strip()
print('official priv len:', len(official), 'head:', official[:30])

conn = psycopg.connect(URI, connect_timeout=15)
cur = conn.cursor()
cur.execute('SELECT id, left(coalesce("privateKey",\'\'), 80), "createdAt" FROM neon_auth.jwks ORDER BY "createdAt"')
rows = cur.fetchall()
print('jwks rows:', len(rows))
for r in rows:
    priv = r[1] or ''
    # _d13 插入格式: '"hexseed"' 即 json 字符串含引号;官方行可能是裸 hex 或同格式
    print(' id:', r[0])
    print('   priv head:', repr(priv))
    print('   created:', r[2])

# 判断:official 文件内容在库中哪行出现(截断比较不可靠,取完整值比较)
cur.execute('SELECT id, "privateKey" FROM neon_auth.jwks')
rows2 = cur.fetchall()
test_id = None
for rid, pk in rows2:
    pk_s = (pk or '').strip().strip('"')
    if pk_s == official.strip().strip('"'):
        print('MATCH official -> keep', rid)
    else:
        print('NOT official -> candidate delete', rid)
        test_id = rid

if test_id:
    cur.execute('DELETE FROM neon_auth.jwks WHERE id=%s', (test_id,))
    print('deleted test jwks row:', test_id)
cur.execute('DROP TABLE IF EXISTS public.demo_rls')
print('dropped demo_rls')
conn.commit()

# 验证
cur.execute('SELECT count(*) FROM neon_auth.jwks')
print('jwks after:', cur.fetchone()[0])
cur.execute("SELECT to_regclass('public.demo_rls')")
print('demo_rls after:', cur.fetchone()[0])
conn.close()
