# -*- coding: utf-8 -*-
"""框架级端点扫描(三域):
A. 父域 OAuth 网关(neonauth.us-east-2.aws.neon.build) 路由字典
B. Data API (apirest) PostgREST 框架端点
C. Keycloak 配置面(console-stage.neon.build/realms/staging-realm)"""
import http.client, ssl, json, time, os, sys

ctx = ssl.create_default_context()
GW = 'neonauth.us-east-2.aws.neon.build'
AP = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
KC = 'console-stage.neon.build'

def req(host, method, path, body=None, headers=None):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=12)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*', 'Content-Type': 'application/json'}
        if headers:
            h.update(headers)
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        conn.close()
        return st, raw.decode('utf-8', 'replace'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}

print('=== A. 父域 OAuth 网关路由字典 ===')
paths = [
    '/', '/health', '/healthz', '/ready', '/live', '/metrics', '/status',
    '/auth', '/auth/', '/auth/oauth', '/auth/oauth/', '/auth/oauth/callback',
    '/auth/oauth/callback/google', '/auth/oauth/callback/github', '/auth/oauth/callback/discord',
    '/auth/oauth/callback/apple', '/auth/oauth/authorize', '/auth/oauth/token', '/auth/oauth/userinfo',
    '/auth/oauth/jwks', '/auth/oauth/logout', '/auth/jwks', '/auth/.well-known', '/auth/.well-known/jwks.json',
    '/auth/sign-in', '/auth/sign-in/social', '/auth/session', '/auth/token', '/auth/get-session',
    '/admin', '/admin/', '/admin/api', '/internal', '/internal/health', '/v1', '/v1/health',
    '/api', '/api/health', '/oauth', '/oauth/', '/oauth/callback/google', '/callback',
    '/.well-known/openid-configuration', '/.well-known/jwks.json', '/favicon.ico', '/robots.txt',
    '/debug', '/actuator', '/actuator/health', '/swagger', '/swagger-ui', '/docs', '/openapi.json',
]
for p in paths:
    st, raw, hdrs = req(GW, 'GET', p)
    if st not in (404, -1) or raw.strip():
        print('[%s] -> %d CT=%s %s' % (p, st, hdrs.get('content-type', '')[:30], raw[:120]))
    time.sleep(0.15)

print('\n=== B. Data API PostgREST 框架端点 ===')
paths2 = [
    '/', '/neondb/rest/v1/', '/neondb/rest/v1', '/neondb/',
    '/neondb/rest/v1/openapi.json', '/neondb/rest/v1/swagger.json', '/neondb/rest/v1/docs',
    '/neondb/rest/v1/rpc', '/neondb/rest/v1/rpc/', '/neondb/rest/v1/health',
    '/neondb/rest/v1/information_schema.tables', '/neondb/rest/v1/pg_catalog.pg_tables',
    '/rest/v1/', '/rest/v1/openapi.json',
]
for p in paths2:
    st, raw, hdrs = req(AP, 'GET', p, headers={'Accept': 'application/json'})
    print('[%s] -> %d CT=%s %s' % (p, st, hdrs.get('content-type', '')[:40], raw[:200]))
    time.sleep(0.2)

print('\n=== C. Keycloak 配置面 ===')
kc_paths = [
    '/realms/staging-realm/.well-known/openid-configuration',
    '/realms/staging-realm/protocol/openid-connect/auth',
    '/realms/staging-realm/protocol/openid-connect/token',
    '/realms/staging-realm/protocol/openid-connect/userinfo',
    '/realms/staging-realm/protocol/openid-connect/logout',
    '/realms/staging-realm/protocol/openid-connect/registrations',
    '/realms/staging-realm/protocol/openid-connect/3p-cookies/step1.html',
    '/realms/staging-realm/account', '/realms/staging-realm/account/',
    '/realms/staging-realm/protocol/saml', '/realms/staging-realm/whoami',
    '/realms/staging-realm/.well-known/openid-configuration/client',
    '/realms/master/.well-known/openid-configuration',
    '/auth/realms/staging-realm/.well-known/openid-configuration',
    '/.well-known/openid-configuration',
]
for p in kc_paths:
    st, raw, hdrs = req(KC, 'GET', p)
    print('[%s] -> %d CT=%s %s' % (p[:70], st, hdrs.get('content-type', '')[:30], raw[:150]))
    time.sleep(0.2)
