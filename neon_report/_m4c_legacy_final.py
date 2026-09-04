# -*- coding: utf-8 -*-
"""legacy user 正常路径(ASCII email) + transfer 后 auth 状态确认"""
import http.client, ssl, json, time, os, sys

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE
keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
KEY = keyj.get('key') or keyj.get('api_key') or keyj.get('token') or list(keyj.values())[0]
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']

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
print('=== [1] transfer 后 auth 集成状态 ===')
st, b = req('GET', '/projects/%s/branches/%s/auth' % (PID, BID), key=KEY)
print('auth 集成 -> %d %s' % (st, b[:250]))
st, b = req('GET', '/projects/%s/branches/%s/auth/oauth_providers' % (PID, BID), key=KEY)
print('oauth -> %d %s' % (st, b[:200]))

print('\n=== [2] legacy user 正常路径(A 项目, ASCII email) ===')
st, b = req('POST', '/projects/auth/user',
            {'project_id': PID, 'auth_provider': 'better_auth',
             'email': 'legacyok%s@gmail.com' % unq, 'name': 'legacy-ok'}, key=KEY)
print('-> %d %s' % (st, b[:200]))
uid = None
try:
    uid = json.loads(b).get('id')
except Exception:
    pass
if uid:
    st, b = req('DELETE', '/projects/%s/auth/users/%s' % (PID, uid), key=KEY)
    print('legacy DELETE -> %d %s' % (st, b[:120]))

print('\n=== [3] 幂等性: transfer 再调一次 ===')
st, b = req('POST', '/projects/auth/transfer_ownership',
            {'project_id': PID, 'auth_provider': 'better_auth'}, key=KEY)
print('-> %d %s' % (st, b[:200]))
