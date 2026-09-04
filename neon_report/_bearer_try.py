# -*- coding: utf-8 -*-
"""测试 Bearer 认证路径(keycloak AccessToken)是否绕过 CSRF 要求"""
import http.client, ssl, json, sys, urllib.parse
sys.path.insert(0, r'D:\scan\neon_report')
from _neon_creds_stage import cookie_str, API_HOST, API_BASE

ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'

# 从 cookie 提取 keycloak_token JSON -> AccessToken
def extract_access_token():
    for c in cookie_str().split(';'):
        c = c.strip()
        if c.startswith('keycloak_token='):
            raw = urllib.parse.unquote(c.split('=', 1)[1])
            d = json.loads(raw)
            return d['AccessToken']
    return None

AT = extract_access_token()
print('access token len:', len(AT) if AT else None)

def try_req(label, use_bearer, csrf=False):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Cookie': cookie_str(), 'X-Bug-Bounty': 'xxbo'}
    if use_bearer:
        h['Authorization'] = 'Bearer ' + AT
    if csrf:
        for c in cookie_str().split(';'):
            c = c.strip()
            if c.startswith('_gorilla_csrf='):
                h['X-CSRF-Token'] = urllib.parse.unquote(c.split('=', 1)[1])
                break
    conn.request('POST', API_BASE + '/projects?org_id=%s' % ORG,
                 body=json.dumps({'project': {'name': 'sec-bearer-1'}}).encode(), headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    print('%-30s -> %d %s' % (label, st, raw[:200]))

try_req('bearer no-csrf', True)
try_req('bearer + csrf', True, True)
