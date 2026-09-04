# -*- coding: utf-8 -*-
"""legacy auth 端点 x better_auth: 存活确认 + body project_id 归属校验行为"""
import http.client, ssl, json, time, os, sys

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE
keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
KEY = keyj.get('key') or keyj.get('api_key') or keyj.get('token') or list(keyj.values())[0]
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']
OTHER = 'damp-term-63384673'
FAKE = 'aaaa-bbbb-12345678'

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

unq = time.strftime('%H%M%S')

print('=== [1] legacy POST /projects/auth/user (better_auth) ===')
created = []
for tag, pid in [('A 自己', PID), ('同org damp-term', OTHER), ('不存在', FAKE), ('缺省', None)]:
    body = {'auth_provider': 'better_auth', 'email': 'legacy%s%s@gmail.com' % (tag[:2], unq),
            'name': 'legacy-test'}
    if pid:
        body['project_id'] = pid
    st, b = req('POST', '/projects/auth/user', body, key=KEY)
    print('[%s %s] -> %d %s' % (tag, pid or '-', st, b[:200]))
    try:
        uid = json.loads(b).get('id')
        if uid:
            created.append((tag, uid))
    except Exception:
        pass
    time.sleep(0.4)
print('创建成功:', created)

print('\n=== [2] legacy POST /projects/auth/keys ===')
for tag, pid in [('A 自己', PID), ('不存在', FAKE)]:
    st, b = req('POST', '/projects/auth/keys', {'project_id': pid, 'auth_provider': 'better_auth'}, key=KEY)
    print('[%s] -> %d %s' % (tag, st, b[:300]))
    time.sleep(0.4)

print('\n=== [3] legacy transfer_ownership ===')
for pid in (PID, FAKE):
    st, b = req('POST', '/projects/auth/transfer_ownership',
                {'project_id': pid, 'auth_provider': 'better_auth'}, key=KEY)
    print('[%s] -> %d %s' % (pid, st, b[:300]))
    time.sleep(0.4)

print('\n=== [4] branch 级 create user 对照(带 name, 应 201) ===')
st, b = req('POST', '/projects/%s/branches/%s/auth/users' % (PID, BID),
            {'email': 'ctrl%s@gmail.com' % unq, 'name': 'ctrl'}, key=KEY)
print('-> %d %s' % (st, b[:200]))
try:
    uid2 = json.loads(b).get('id')
except Exception:
    uid2 = None

print('\n=== [5] 清理 legacy 创建的 A 项目用户 ===')
for tag, uid in created:
    if tag == 'A 自己':
        st, b = req('DELETE', '/projects/%s/auth/users/%s' % (PID, uid), key=KEY)
        print('legacy DELETE [%s %s] -> %d %s' % (tag, uid, st, b[:120]))
    else:
        print('damp-term 用户不动(非本项目):', uid)
if uid2:
    st, b = req('DELETE', '/projects/%s/branches/%s/auth/users/%s' % (PID, BID, uid2), key=KEY)
    print('branch DELETE -> %d %s' % (st, b[:120]))
