# -*- coding: utf-8 -*-
"""transfer initiated 后: 完整 auth 详情 + auth 域功能只读验证"""
import http.client, ssl, json, time, os, sys

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def req(host, method, path, body=None, headers=None, raw_headers=False):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    hdrs = r.headers
    conn.close()
    if raw_headers:
        return st, raw, hdrs
    return st, raw

print('=== [1] 完整 auth 集成详情 ===')
st, raw = req(API_HOST, 'GET', API_BASE + '/projects/%s/branches/%s/auth' % (PID, BID),
              headers={'Cookie': cookie_str(), 'X-Bug-Bounty': 'xxbo'})
print('%d %s' % (st, raw.decode('utf-8', 'replace')))

print('\n=== [2] auth 域功能只读验证 ===')
# 真 cookie 会话
c = cookie_str()
st, raw = req(NA, 'GET', '/neondb/auth/token', headers={'Cookie': c, 'X-Bug-Bounty': 'xxbo'})
tok = ''
try:
    tok = json.loads(raw).get('token', '')[:60]
except Exception:
    pass
print('GET /token -> %d (%s...)' % (st, tok))
st, raw = req(NA, 'GET', '/neondb/auth/get-session', headers={'Cookie': c, 'X-Bug-Bounty': 'xxbo'})
print('GET /get-session -> %d %s' % (st, raw.decode('utf-8', 'replace')[:150]))

# 密码登录(自己账号, 无破坏): 验证 sign-in 流程仍活
st, raw = req(NA, 'POST', '/neondb/auth/sign-in/email',
              {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'},
              {'Origin': 'http://localhost:3000', 'Content-Type': 'application/json'})
print('POST sign-in/email -> %d %s' % (st, raw.decode('utf-8', 'replace')[:150]))
