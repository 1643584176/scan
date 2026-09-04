# -*- coding: utf-8 -*-
"""三面探测:
1. Logs query(API key POST, 无 CSRF 要求) - logql 注入面初探
2. S3 endpoint 匿名认证判定
3. AI Gateway 匿名认证判定"""
import http.client, ssl, json, time, os, sys

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE
keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
KEY = keyj.get('key') or keyj.get('api_key') or keyj.get('token') or list(keyj.values())[0]
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']
S3 = 'br-wandering-field-w2ob6mpn.storage.c-1.us-east-2.aws.neon.build'
AI = 'br-wandering-field-w2ob6mpn-api.ai.c-1.us-east-2.aws.neon.build'

def req(host, method, path, body=None, headers=None):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
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

print('=== [1] Logs query (API key) ===')
def logq(body):
    st, raw, hdrs = req(API_HOST, 'POST', API_BASE + '/projects/%s/branches/%s/logs/query' % (PID, BID), body,
                        {'Authorization': 'Bearer ' + str(KEY), 'X-Bug-Bounty': 'xxbo'})
    return st, raw

for tag, body in [
    ('空查询', {'since': '1h', 'limit': 5}),
    ('body_contains', {'since': '1h', 'limit': 5, 'body_contains': 'select'}),
    ('logql 简单', {'since': '1h', 'limit': 5, 'logql': '{service_name="neondb"} |= "select"'}),
    ('logql 复杂', {'since': '1h', 'limit': 5, 'logql': '{service_name=~".+"} | line_format "{{.message}}"'}),
]:
    st, raw = logq(body)
    print('[%s] -> %d %s' % (tag, st, raw[:400]))
    time.sleep(0.3)

print('\n=== [2] S3 匿名判定 ===')
for tag, path, method in [
    ('ListBuckets', '/', 'GET'),
    ('ListObjects', '/br-wandering-field-w2ob6mpn', 'GET'),
    ('ListObjects v2', '/br-wandering-field-w2ob6mpn?list-type=2', 'GET'),
    ('根 HEAD', '/', 'HEAD'),
]:
    st, raw, hdrs = req(S3, method, path)
    print('[%s %s] -> %d CT=%s %s' % (tag, path[:40], st, hdrs.get('content-type', ''), raw[:250]))
    time.sleep(0.3)

print('\n=== [3] AI Gateway 匿名判定 ===')
for tag, path in [
    ('models', '/ai-gateway/openai/v1/models'),
    ('models alt', '/openai/v1/models'),
    ('v1/models', '/v1/models'),
    ('根', '/'),
]:
    st, raw, hdrs = req(AI, 'GET', path)
    print('[%s %s] -> %d CT=%s %s' % (tag, path, st, hdrs.get('content-type', ''), raw[:300]))
    time.sleep(0.3)
