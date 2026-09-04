# -*- coding: utf-8 -*-
"""收尾清理:删 probe-x1 org + 确认 neon_auth 无残留邀请/幽灵数据"""
import http.client, ssl, json, time, psycopg

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
s = json.load(open('_na_sess.json'))

def req(method, path, body=None, cookie=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
             'Origin': ORIGIN}
        if cookie:
            h['Cookie'] = cookie
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status; conn.close()
        return st, raw[:300]
    except Exception as e:
        return 0, str(e).encode()[:120]

st, raw = req('POST', '/neondb/auth/organization/delete',
              {'organizationId': 'cb082192-236a-482e-82d5-43a2c778facb'}, cookie=s['ck1'])
print('[delete probe-x1] -> %d | %s' % (st, raw.decode(errors='replace')[:200]), flush=True)

# PG 侧确认状态
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=15)
cur = conn.cursor()
for t in ['organization', 'member', 'invitation']:
    cur.execute('SELECT count(*) FROM neon_auth.%s' % t)
    print('%s rows: %d' % (t, cur.fetchone()[0]))
cur.execute('SELECT count(*) FROM neon_auth.user')
print('user rows: %d' % cur.fetchone()[0])
conn.close()
