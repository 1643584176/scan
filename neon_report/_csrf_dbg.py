# -*- coding: utf-8 -*-
"""CSRF 调试:测试 header 值/Origin 组合"""
import http.client, ssl, json, sys, urllib.parse
sys.path.insert(0, r'D:\scan\neon_report')
from _neon_creds_stage import cookie_str, API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'
RAW_COOKIE = cookie_str()

def csrf_val():
    for c in RAW_COOKIE.split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf='):
            return c.split('=', 1)[1]
    return None

def try_req(label, csrf_hdr, origin=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Cookie': RAW_COOKIE, 'X-Bug-Bounty': 'xxbo'}
    if csrf_hdr:
        h['X-CSRF-Token'] = csrf_hdr
    if origin:
        h['Origin'] = origin
        h['Referer'] = origin + '/'
    conn.request('POST', API_BASE + '/projects?org_id=%s' % ORG,
                 body=json.dumps({'project': {'name': 'sec-csrf-t'}}).encode(), headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    print('%-28s -> %d %s' % (label, st, raw[:120]))

cv = csrf_val()
print('csrf cookie len:', len(cv))
try_req('no csrf hdr', None)
try_req('raw cookie val', cv)
try_req('unquote', urllib.parse.unquote(cv))
try_req('unquote+origin', urllib.parse.unquote(cv), 'https://console-stage.neon.build')
try_req('raw+origin', cv, 'https://console-stage.neon.build')
