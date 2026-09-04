# -*- coding: utf-8 -*-
"""API key 状态验证: 带/不带 org_id + cookie 认证对照"""
import http.client, ssl, json, os, sys, re

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
API_HOST = 'console-stage.neon.build'
API_BASE = '/api/v2'
keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
if isinstance(keyj, dict):
    KEY = keyj.get('key') or keyj.get('api_key') or keyj.get('token') or list(keyj.values())[0]
else:
    KEY = keyj
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
ORG = ctxj.get('org', '')

def req(method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw.decode('utf-8', 'replace')

print('key 前12位:', str(KEY)[:12], ' org:', ORG)
st, b = req('GET', '/projects?org_id=' + ORG, headers={'Authorization': 'Bearer ' + str(KEY)})
print('[key + org_id] -> %d %s' % (st, b[:200]))
st, b = req('GET', '/projects', headers={'Authorization': 'Bearer ' + str(KEY)})
print('[key 无 org_id] -> %d %s' % (st, b[:200]))

# cookie 认证对照
from _neon_creds_stage import COOKIE_RAW
st, b = req('GET', '/projects', headers={'Cookie': COOKIE_RAW})
print('[cookie] -> %d %s' % (st, b[:200]))
st, b = req('GET', '/projects?org_id=' + ORG, headers={'Cookie': COOKIE_RAW})
print('[cookie + org_id] -> %d %s' % (st, b[:200]))
