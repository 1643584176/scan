# -*- coding: utf-8 -*-
"""1) 控制面 auth config: enabledPlugins 精确值
2) nauth organization 插件端点(带 body 精确探测)
3) nauth sign-up/email 注册流程(emailVerified=false 预注册可行性)"""
import http.client, ssl, json, time, sys

sys.path.insert(0, '.')
from _neon_creds_stage import cookie_str
import json
ctxd = json.load(open('_ctx.json', encoding='utf-8'))
PID, BID, ORG_ID = ctxd['pid'], ctxd['bid'], ctxd['org']

ctx = ssl.create_default_context()

def req_cp(method, path, body=None):
    try:
        conn = http.client.HTTPSConnection('console-stage.neon.build', context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Content-Type': 'application/json', 'Cookie': cookie_str(), 'X-Bug-Bounty': 'xxbo'}
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        conn.close()
        return st, raw.decode('utf-8', 'replace')
    except Exception as e:
        return -1, 'EXC %s' % e

def req_na(method, path, body=None, cookie=None):
    try:
        conn = http.client.HTTPSConnection('ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build', context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if cookie:
            h['Cookie'] = cookie
        conn.request(method, '/neondb/auth' + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        conn.close()
        return st, raw.decode('utf-8', 'replace'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}

print('=== [1] 控制面 auth config ===', flush=True)
for p in ['/api/v2/projects/%s/auth/config' % PID,
          '/api/v2/projects/%s/auth' % PID,
          '/api/v2/branches/%s/auth/config' % BID]:
    st, raw = req_cp('GET', p)
    print('[%s] -> %d %s' % (p[-40:], st, raw[:500].replace('\n', ' ')), flush=True)
    time.sleep(0.3)

print('\n=== [2] nauth organization 端点(匿名 vs na2) ===', flush=True)
# na2 登录
st0, raw0, hdrs0 = req_na('POST', '/sign-in/email', {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'})
ck = ''
sc0 = hdrs0.get('set-cookie', '')
for part in sc0.split(','):
    kv = part.strip().split(';')[0]
    if '=' in kv:
        k, v = kv.split('=', 1)
        ck = ck + ('; ' if ck else '') + '%s=%s' % (k.strip(), v.strip())
print('na2 sign-in:', st0, 'ck:', ck[:60], flush=True)

org_probes = [
    ('POST', '/organization/create', {'name': 'sec-n10-probe'}),
    ('GET', '/organization/list', None),
    ('POST', '/organization/list', {}),
    ('GET', '/organization', None),
    ('POST', '/organization/members', {}),
    ('POST', '/organization/invite-member', {'email': 'x@y.z', 'role': 'admin'}),
    ('POST', '/organization/accept-invitation', {'invitationId': 'x'}),
    ('POST', '/organization/get-invitation', {'invitationId': 'x'}),
    ('POST', '/organization/roles', {}),
    ('GET', '/organization/roles', None),
]
for method, p, b in org_probes:
    st, raw, _ = req_na(method, p, b, cookie=ck or None)
    print('[%s %s anon=%s] -> %d %s' % (method, p, 'auth' if ck else 'anon', st, raw[:180].replace('\n', ' ')), flush=True)
    time.sleep(0.25)

print('\n=== [3] sign-up/email 注册(预注册行 emailVerified 状态) ===', flush=True)
st9, raw9, _ = req_na('POST', '/sign-up/email', {'email': 'libobo1229+secn10@gmail.com', 'password': 'SecTest!2026pass2', 'name': 'sec-n10'})
print('[sign-up/email] -> %d %s' % (st9, raw9[:300].replace('\n', ' ')), flush=True)
