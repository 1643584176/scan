# -*- coding: utf-8 -*-
"""org/auth 端点 POST 空体探测(400 参数错=存在,404=不存在,无副作用)"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
toks = json.load(open('_na_tokens.json'))

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
        return st, raw[:200]
    except Exception as e:
        return 0, str(e).encode()[:100]

paths = [
    ('/neondb/auth/organization/create', 'POST', toks['na1']),
    ('/neondb/auth/organization/update', 'POST', toks['na1']),
    ('/neondb/auth/organization/delete', 'POST', toks['na1']),
    ('/neondb/auth/organization/invite-member', 'POST', toks['na1']),
    ('/neondb/auth/organization/reject-invitation', 'POST', toks['na2']),
    ('/neondb/auth/organization/cancel-invitation', 'POST', toks['na1']),
    ('/neondb/auth/organization/remove-member', 'POST', toks['na1']),
    ('/neondb/auth/organization/update-member-role', 'POST', toks['na1']),
    ('/neondb/auth/organization/leave', 'POST', toks['na1']),
    ('/neondb/auth/organization/set-active', 'POST', toks['na1']),
    ('/neondb/auth/update-user', 'POST', toks['na1']),
    ('/neondb/auth/change-password', 'POST', toks['na1']),
    ('/neondb/auth/forget-password', 'POST', toks['na1']),
    ('/neondb/auth/sign-out', 'POST', toks['na1']),
    ('/neondb/auth/revoke-sessions', 'POST', toks['na1']),
    ('/neondb/auth/revoke-other-sessions', 'POST', toks['na1']),
]
for p, m, tok in paths:
    st, raw = na_req(m, p, {}, token=tok)
    print('%-55s -> %d | %s' % (p, st, raw.decode(errors='replace')[:110]), flush=True)
    time.sleep(0.5)
