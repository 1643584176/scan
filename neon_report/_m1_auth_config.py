# -*- coding: utf-8 -*-
"""控制面 auth 配置全量读取(A 项目): config/plugins/oauth/domains/webhooks 等
目的: 完整配置画像 -> 找现代浏览器可打的新攻击面"""
import http.client, ssl, json, time, os, sys, re, html

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']

def req(host, method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw

def get_auth_cfg(path):
    st, raw = req(API_HOST, 'GET', API_BASE + path,
                  headers={'Cookie': cookie_str(), 'X-Bug-Bounty': 'xxbo', 'User-Agent': 'Mozilla/5.0'})
    return st, raw.decode('utf-8', 'replace')

BASE = '/projects/%s/branches/%s' % (PID, BID)
paths = [
    ('auth 集成详情', '/auth'),
    ('config', '/auth/config'),
    ('plugins', '/auth/plugins'),
    ('oauth_providers', '/auth/oauth_providers'),
    ('domains(redirect白名单)', '/auth/domains'),
    ('allow_localhost', '/auth/allow_localhost'),
    ('email_and_password', '/auth/email_and_password'),
    ('email_provider', '/auth/email_provider'),
    ('webhooks', '/auth/webhooks'),
    ('plugins/organization', '/auth/plugins/organization'),
    ('plugins/magic-link', '/auth/plugins/magic-link'),
    ('plugins/phone-number', '/auth/plugins/phone-number'),
]
for tag, p in paths:
    st, body = get_auth_cfg(BASE + p)
    print('=== %s -> %d' % (tag, st))
    print('  %s' % body[:700])
    print()
    time.sleep(0.3)
