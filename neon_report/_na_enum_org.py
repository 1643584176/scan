# -*- coding: utf-8 -*-
"""保存双 token + org 插件端点面枚举(GET 探测)"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
TOK1 = 'nKQmRW3AaNnld5tdI6dNYLQzs0sjbKoA'   # +na1
TOK2 = 'KKDtOtdnWD7dIucRR8uJJLlm4g3BagM4'   # +na2
json.dump({'na1': TOK1, 'na2': TOK2}, open('_na_tokens.json', 'w'))
print('tokens saved')

def na_req(method, path, body=None, token=None, origin='http://localhost:3000'):
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
        return st, raw[:250]
    except Exception as e:
        return 0, str(e).encode()[:120]

paths = [
    '/neondb/auth/organization/create', '/neondb/auth/organization/list',
    '/neondb/auth/organization/update', '/neondb/auth/organization/delete',
    '/neondb/auth/organization/invite-member', '/neondb/auth/organization/accept-invitation',
    '/neondb/auth/organization/reject-invitation', '/neondb/auth/organization/cancel-invitation',
    '/neondb/auth/organization/remove-member', '/neondb/auth/organization/update-member-role',
    '/neondb/auth/organization/member/role', '/neondb/auth/organization/leave',
    '/neondb/auth/organization/check-end-slug', '/neondb/auth/organization/check-slug',
    '/neondb/auth/update-user', '/neondb/auth/change-password', '/neondb/auth/forget-password',
    '/neondb/auth/reset-password', '/neondb/auth/verify-email', '/neondb/auth/revoke-sessions',
    '/neondb/auth/revoke-other-sessions', '/neondb/auth/sign-in/email', '/neondb/auth/sign-out',
]
for p in paths:
    st, raw = na_req('GET', p, token=TOK1)
    print('%-55s -> %d | %s' % (p, st, raw.decode(errors='replace')[:90]), flush=True)
    time.sleep(0.4)
