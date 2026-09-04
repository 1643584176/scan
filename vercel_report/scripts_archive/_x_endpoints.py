# -*- coding: utf-8 -*-
"""sandbox REST API 端点枚举 (v44e): 只读 GET 为主, 找未探测端点"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

# 建一个沙箱供 session 级端点探测
NAME = 'enumtest44'
c, r = api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": NAME}, 60)
print('create:', c, flush=True)
sid = json.loads(r)['sandbox']['currentSessionId']
time.sleep(3)

GET_CANDS = [
    '/v2/sandboxes/%s' % NAME,
    '/v2/sandboxes/%s/status' % NAME,
    '/v2/sandboxes/%s/env' % NAME,
    '/v2/sandboxes/%s/network-policy' % NAME,
    '/v2/sandboxes/%s/sessions' % NAME,
    '/v2/sandboxes/%s/snapshots' % NAME,
    '/v2/sandboxes/%s/fs' % NAME,
    '/v2/sandboxes/%s/files' % NAME,
    '/v2/sandboxes/sessions/%s' % sid,
    '/v2/sandboxes/sessions/%s/status' % sid,
    '/v2/sandboxes/sessions/%s/fs' % sid,
    '/v2/sandboxes/sessions/%s/files' % sid,
    '/v2/sandboxes/sessions/%s/env' % sid,
    '/v2/sandboxes/sessions/%s/network-policy' % sid,
    '/v2/sandboxes/sessions/%s/events' % sid,
    '/v2/sandboxes/sessions/%s/snapshots' % sid,
    '/v2/sandboxes/sessions/%s/port' % sid,
    '/v2/sandboxes/sessions/%s/ports' % sid,
    '/v2/sandboxes/sessions/%s/snapshot' % sid,
    '/v2/sandboxes/sessions/%s/interactive' % sid,
    '/v2/sandboxes/sessions/%s/exec' % sid,
]
for ep in GET_CANDS:
    c, r = api('GET', ep + '?teamId=%s&projectId=%s' % (TEAM, PROJ), timeout=30)
    tag = ep.split('?')[0][:55]
    print('%-58s -> %d %s' % (tag, c, (r or '')[:120].replace('\n', ' ')), flush=True)
    time.sleep(0.4)

api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
print('CLEANED', flush=True)
