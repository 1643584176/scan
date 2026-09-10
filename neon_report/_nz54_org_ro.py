# -*- coding: utf-8 -*-
"""T7: Organizations 面只读收尾 (6 req) — members/invitations/vpc/spending/api_keys"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
OID = 'org-flat-dawn-91601224'
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
            print('== %-28s -> %d  %s' % (tag, r.status, raw[:350].decode('utf-8', 'replace')))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

req('org 详情', '/organizations/%s' % OID)
req('members 列表', '/organizations/%s/members' % OID)
req('invitations', '/organizations/%s/invitations' % OID)
req('org api_keys', '/organizations/%s/api_keys' % OID)
req('billing spending_limit', '/organizations/%s/billing/spending_limit' % OID)
req('vpc endpoints', '/organizations/%s/vpc/vpc_endpoints' % OID)
