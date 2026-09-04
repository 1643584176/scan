# -*- coding: utf-8 -*-
"""legacy auth 端点存活与归属校验探测(应 2026-03-01 移除, 现已过期 6 个月)
- POST /projects/auth/user    body project_id -> 归属校验行为
- POST /projects/auth/keys    body project_id -> 建 key
- POST /projects/auth/transfer_ownership
- GET  /projects/auth/email_server
- GET/POST /projects/{pid}/auth/domains (legacy domains)
对照: damp-term(同 org 他项目) / 不存在项目 id / 无 project_id"""
import http.client, ssl, json, time, os, sys

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE
keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
KEY = keyj.get('key') or list(keyj.values())[0]
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID = ctxj['pid']
OTHER = 'damp-term-63384673'   # 同 org 历史残留项目
FAKE = 'aaaa-bbbb-12345678'    # 不存在

def req(method, path, body=None, key=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'X-Bug-Bounty': 'xxbo'}
    if key:
        h['Authorization'] = 'Bearer %s' % key
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw.decode('utf-8', 'replace')

print('=== [0] GET /projects (key 权限范围确认) ===')
st, b = req('GET', '/projects?org_id=' + ctxj.get('org', ''), key=KEY)
print('%d %s' % (st, b[:600]))
print('damp-term 在列表:', 'damp-term-63384673' in b)

print('\n=== [1] legacy POST /projects/auth/user (body project_id 归属矩阵) ===')
for tag, pid in [('A 自己', PID), ('同org damp-term', OTHER), ('不存在', FAKE), ('缺省', None)]:
    body = {'auth_provider': 'neon_auth', 'email': 'na5x%d@gmail.com' % (time.time_ns() % 100000)}
    if pid:
        body['project_id'] = pid
    st, b = req('POST', '/projects/auth/user', body, key=KEY)
    print('[%s] -> %d %s' % (tag, st, b[:250]))
    time.sleep(0.4)

print('\n=== [2] legacy POST /projects/auth/keys ===')
for tag, pid in [('A 自己', PID), ('不存在', FAKE)]:
    st, b = req('POST', '/projects/auth/keys', {'project_id': pid, 'auth_provider': 'neon_auth'}, key=KEY)
    print('[%s] -> %d %s' % (tag, st, b[:250]))
    time.sleep(0.4)

print('\n=== [3] legacy transfer_ownership ===')
st, b = req('POST', '/projects/auth/transfer_ownership', {}, key=KEY)
print('[] -> %d %s' % (st, b[:250]))
time.sleep(0.3)

print('\n=== [4] legacy GET email_server / domains ===')
st, b = req('GET', '/projects/%s/auth/email_server' % PID, key=KEY)
print('email_server -> %d %s' % (st, b[:300]))
time.sleep(0.3)
st, b = req('GET', '/projects/%s/auth/domains' % PID, key=KEY)
print('domains -> %d %s' % (st, b[:200]))
time.sleep(0.3)

print('\n=== [5] branch 级 create user 对照(应正常 201) ===')
st, b = req('POST', '/projects/%s/branches/%s/auth/users' % (PID, ctxj['bid']),
            {'email': 'na5ctrl%d@gmail.com' % (time.time_ns() % 100000)}, key=KEY)
print('-> %d %s' % (st, b[:200]))
