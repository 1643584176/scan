# -*- coding: utf-8 -*-
"""pg_session_jwt 直连语义实测:JWK GUC 状态 / request.jwt.claims fallback"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

print('1) jwk GUC:', q("SELECT current_setting('pg_session_jwt.jwk', true)"), flush=True)
print('2) jwt GUC:', q("SELECT current_setting('pg_session_jwt.jwt', true)"), flush=True)
print('3) auth.user_id() 初始:', q('SELECT auth.user_id()'), flush=True)
print('4) auth.jwt() 初始:', q('SELECT auth.jwt()'), flush=True)

# 5) 尝试 SET pg_session_jwt.jwk(Backend context 应被拒)
print('5) SET jwk:', q("SET pg_session_jwt.jwk = '{}'"), flush=True)

# 6) SET request.jwt.claims 后 user_id()
print('6) SET claims:', q("SET request.jwt.claims = '{\"sub\":\"fake-user-123\",\"role\":\"neondb_owner\"}'"), flush=True)
print('7) auth.user_id() after claims:', q('SELECT auth.user_id()'), flush=True)
print('8) auth.jwt() after claims:', q('SELECT auth.jwt()'), flush=True)

# 9) SET pg_session_jwt.jwt 后(未设 JWK → 应验签失败或 fallback)
print('9) SET jwt:', q("SET pg_session_jwt.jwt = 'eyJhbGciOiJub25lIn0.eyJzdWIiOiJ4In0.'"), flush=True)
print('10) auth.user_id() after jwt:', q('SELECT auth.user_id()'), flush=True)

# 11) 若 jwk 可设,设一个 Ed25519 公钥再自签?先看 5 的结果再决定
print('11) auth.session():', q('SELECT auth.session()'), flush=True)
print('12) auth.uid():', q('SELECT auth.uid()'), flush=True)

# 13) 函数权限:public/anon 能否执行
cur.execute("SELECT p.proname, pg_get_userbyid(p.proowner), a.privilege_type FROM pg_proc p CROSS JOIN LATERAL aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a WHERE p.pronamespace = 'auth'::regnamespace AND p.proname IN ('jwt_session_init','user_id','uid','jwt','session')")
for r in cur.fetchall():
    print('proc acl:', r, flush=True)

# 14) GUC 可 SET 性对非 owner(authenticated 密码从控制面重置后测,先看 owner)
conn.close()
print('done', flush=True)
