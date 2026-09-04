# -*- coding: utf-8 -*-
"""Beta 面存活探测: ai_gateway/storage/snapshots/logs + 内部域可达性"""
import http.client, ssl, json, time, os, sys, socket

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, cookie_str
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']

def req(host, method, path, body=None, headers=None, port=443):
    try:
        conn = http.client.HTTPSConnection(host, port=port, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if headers:
            h.update(headers)
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        conn.close()
        return st, raw.decode('utf-8', 'replace')
    except Exception as e:
        return -1, 'EXC %s' % e

BASE = '/projects/%s/branches/%s' % (PID, BID)
hdrs = {'Cookie': cookie_str(), 'X-Bug-Bounty': 'xxbo'}

print('=== [1] 控制面 beta 端点探活 ===')
for tag, p, method, body in [
    ('ai_gateway', BASE + '/ai_gateway', 'GET', None),
    ('storage', BASE + '/storage', 'GET', None),
    ('snapshots', '/projects/%s/snapshots' % PID, 'GET', None),
    ('logs/fields', BASE + '/logs/fields', 'GET', None),
    ('logs/query 空', BASE + '/logs/query', 'POST', {}),
    ('logs/query 1h', BASE + '/logs/query', 'POST', {'since': '1h', 'limit': 5}),
]:
    st, b = req(API_HOST, method, API_BASE + p, body, hdrs)
    print('[%s] -> %d %s' % (tag, st, b[:300]))
    time.sleep(0.3)

print('\n=== [2] 内部域可达性(DNS) ===')
for d in ('br-cool-moon-42-api.ai.c-2.local.neon.build', 'br-cool-moon-42.storage.c-2.local.neon.build',
          'ai.c-2.local.neon.build', 'storage.c-2.local.neon.build'):
    try:
        ip = socket.gethostbyname(d)
        print('[%s] 解析 -> %s' % (d, ip))
    except Exception as e:
        print('[%s] 解析失败 %s' % (d, e))

print('\n=== [3] 若 DNS 可解析则匿名探活 ===')
for d in ('ep-crimson-fog-w2gucld1-api.ai.us-east-2.aws.neon.build',
          'ep-crimson-fog-w2gucld1.storage.us-east-2.aws.neon.build'):
    try:
        ip = socket.gethostbyname(d)
        print('[%s] 解析 -> %s' % (d, ip))
    except Exception as e:
        print('[%s] 解析失败 %s' % (d, e))
