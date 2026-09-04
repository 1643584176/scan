# -*- coding: utf-8 -*-
"""清理: 删除 B 测试项目 broad-violet-25805528 + 确认 A 无残留"""
import http.client, ssl, json, os, sys

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str
keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
KEY = keyj.get('key') or list(keyj.values())[0]
PID2 = 'broad-violet-25805528'

def req(method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw

# 1. 删除 B 项目(API key)
st, raw = req('DELETE', '/api/v2/projects/%s' % PID2,
              headers={'Authorization': 'Bearer ' + str(KEY), 'X-Bug-Bounty': 'xxbo'})
print('DELETE project B -> %d %s' % (st, raw.decode(errors='replace')[:150]))

# 2. 确认列表
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
st, raw = req('GET', '/api/v2/projects?org_id=%s' % ctxj['org'],
              headers={'Authorization': 'Bearer ' + str(KEY), 'X-Bug-Bounty': 'xxbo'})
try:
    ps = json.loads(raw).get('projects', [])
    print('剩余项目:', [(p['id'], p['name']) for p in ps])
except Exception:
    print(raw.decode(errors='replace')[:300])
