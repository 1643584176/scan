# -*- coding: utf-8 -*-
"""Data API 面侦察[1]:neon_auth.jwks 私钥可得性(不打印全文,只打印元信息)
+ project_config 结构 + session 里 JWT 的 payload 样例(截断)。
零破坏:全只读。"""
import psycopg, json

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:300]

print('=== [1] jwks 表结构 ===')
print(q("""SELECT a.attname, format_type(a.atttypid, a.atttypmod)
          FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
          WHERE c.relname='jwks' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum"""))

print('\n=== [2] jwks 内容(元信息:字段名/类型/长度,值打码) ===')
rows = q('SELECT * FROM neon_auth.jwks')
if isinstance(rows, list):
    cols = [d[0] for d in cur.description]
    for r in rows:
        meta = []
        for c, v in zip(cols, r):
            if v is None:
                meta.append('%s=None' % c)
            elif isinstance(v, (bytes, bytearray)):
                meta.append('%s=bytes(%d)' % (c, len(v)))
            elif isinstance(v, str) and len(v) > 40:
                meta.append('%s=str(%d) head=%s...' % (c, len(v), v[:24].replace('\n', '\\n')))
            else:
                meta.append('%s=%r' % (c, str(v)[:60]))
        print('  row:', '; '.join(meta))
else:
    print(' ', rows)

print('\n=== [3] project_config 表(打码) ===')
rows = q('SELECT * FROM neon_auth.project_config')
if isinstance(rows, list):
    cols = [d[0] for d in cur.description]
    for r in rows:
        for c, v in zip(cols, r):
            if v is None:
                continue
            s = str(v)
            if len(s) > 80 or any(k in c.lower() for k in ('secret', 'key', 'jwt', 'url')):
                print('  %s = %s... (len=%d)' % (c, s[:48].replace('\n', ' '), len(s)))
            else:
                print('  %s = %s' % (c, s[:120]))
else:
    print(' ', rows)

print('\n=== [4] session 里 token 样例(找 JWT 格式,payload 截断) ===')
rows = q('SELECT id, "userId", token, "expiresAt" FROM neon_auth.session ORDER BY "createdAt" DESC LIMIT 3')
if isinstance(rows, list):
    import base64
    for r in rows:
        tok = r[2] or ''
        head = 'not-jwt'
        if tok.count('.') == 2:
            try:
                p = tok.split('.')[1]
                p += '=' * (-len(p) % 4)
                head = json.dumps(json.loads(base64.urlsafe_b64decode(p)), ensure_ascii=False)[:400]
            except Exception as e:
                head = 'parse-err %s' % e
        print('  session id=%s user=%s token(head=%d): %s...' % (str(r[0])[:8], str(r[1])[:8], len(tok), head))
else:
    print(' ', rows)

conn.close()
