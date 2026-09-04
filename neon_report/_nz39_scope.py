# -*- coding: utf-8 -*-
"""scope 确定: A key 对 users/me, projects 列表, A/B 项目只读探测 (6 req, 只读)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
PB = 'broad-violet-25805528'
ctx = ssl.create_default_context()

def req(tag, path):
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request('GET', API_BASE + path, headers=h)
            r = c.getresponse(); raw = r.read(); c.close()
            print('== %-30s -> %d  %s' % (tag, r.status, raw[:500].decode('utf-8', 'replace')))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

req('users/me', '/users/me')
req('projects 列表', '/projects')
req('A 项目', '/projects/%s' % PA)
req('B 项目(跨项目探测)', '/projects/%s' % PB)
req('B connection_uri', '/projects/%s/connection_uri' % PB)
req('B branches', '/projects/%s/branches' % PB)
