# -*- coding: utf-8 -*-
"""拿 roles + 连接串(role_name)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'

def req(tag, path):
    c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    c.request('GET', API_BASE + path, headers=h)
    r = c.getresponse(); raw = r.read()
    c.close()
    print('\n== %s -> %d' % (tag, r.status))
    print(raw[:1200].decode('utf-8', errors='replace'))

req('roles', '/projects/%s/branches/br-wandering-field-w2ob6mpn/roles' % P)
