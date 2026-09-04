# -*- coding: utf-8 -*-
"""控制面 auth/users role 设置 -> JWT role claim 变化? -> Data API SET ROLE 影响?
测试于 A 项目(orange-sun), 测完改回 user"""
import http.client, ssl, json, time, os, sys, re, html, base64, psycopg

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'

def req(host, method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw

def ctl_req(method, path, body=None):
    """控制面带 CSRF 的请求"""
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r = conn.getresponse()
    body0 = r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    txt = body0.decode('utf-8', 'replace')
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m.group(1)) if m else None
    parts = []
    for c in cookie_str().split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    conn = http.client.HTTPSConnection(API_HOST, timeout=25)
    hdrs = {'Cookie': '; '.join(parts), 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    if csrf:
        hdrs['X-CSRF-Token'] = csrf
    conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=hdrs)
    r = conn.getresponse()
    data = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, data

def auth_jwt():
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
    conn.request('POST', '/neondb/auth/sign-in/email',
                 body=json.dumps({'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'}).encode(),
                 headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'Origin': 'http://localhost:3000'})
    r = conn.getresponse(); r.read()
    cks = r.headers.get_all('Set-Cookie')
    conn.close()
    cook = '; '.join(c.split(';')[0] for c in cks)
    st, raw = req(NA, 'GET', '/neondb/auth/token', headers={'Cookie': cook})
    return json.loads(raw).get('token', '')

def b64d(s):
    return json.loads(base64.urlsafe_b64decode(s + '=' * (-len(s) % 4)))

uid = None
print('=== [0] DB 查目标用户 ===')
try:
    dbc = psycopg.connect('postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb',
                          connect_timeout=20)
    dbc.autocommit = True
    cur = dbc.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='neon_auth'")
    print('  tables:', [r[0] for r in cur.fetchall()])
    for t in ('user', 'users_sync', 'users'):
        try:
            cur.execute('SELECT id, email, role FROM neon_auth.%s LIMIT 50' % t)
            rows = cur.fetchall()
            hits = [r for r in rows if r[1] and 'na2' in r[1]]
            if hits:
                print('  %s total=%d hits=%s' % (t, len(rows), hits[:3]))
                uid = hits[0][0]
                break
        except Exception as e:
            print('  %s err: %s' % (t, str(e)[:100]))
    dbc.close()
except Exception as e:
    print('  DB ERR: %s' % str(e)[:150])

if not uid:
    print('!! DB 未找到用户, 跳过')
    sys.exit(0)

print('target uid =', uid)

print('\n=== [1] PUT role -> neondb_owner ===')
st, body = ctl_req('PUT', API_BASE + '/projects/%s/branches/%s/auth/users/%s/role' % (PID, BID, uid),
                   {'roles': ['neondb_owner']})
print('PUT role -> %d %s' % (st, body[:200]))
time.sleep(2)

print('\n=== [2] 新 JWT role claim ===')
jwt = auth_jwt()
pl = b64d(jwt.split('.')[1])
print('JWT role claim =', pl.get('role'))

print('\n=== [3] Data API 探测 ===')
for path, hdrs in [('/user?select=email&limit=2', {'Accept-Profile': 'neon_auth'}),
                   ('/zz_roleprobe?limit=1', None)]:
    hh = {'Authorization': 'Bearer ' + jwt}
    if hdrs:
        hh.update(hdrs)
    st, raw = req(DA, 'GET', '/neondb/rest/v1' + path, headers=hh)
    print('  GET %s -> %d %s' % (path.split('?')[0], st, raw.decode(errors='replace')[:150]))
    time.sleep(0.3)

print('\n=== [4] 恢复 role -> user ===')
st, body = ctl_req('PUT', API_BASE + '/projects/%s/branches/%s/auth/users/%s/role' % (PID, BID, uid),
                   {'roles': ['user']})
print('restore -> %d %s' % (st, body[:150]))
time.sleep(2)
jwt2 = auth_jwt()
pl2 = b64d(jwt2.split('.')[1])
print('restored JWT role =', pl2.get('role'))
