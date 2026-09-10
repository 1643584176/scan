# -*- coding: utf-8 -*-
"""T6: 残留确认(T分支/快照) + Functions/Buckets 探测 (5 req 只读)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
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
            print('== %-28s -> %d  %s' % (tag, r.status, raw[:300].decode('utf-8', 'replace')))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

req('T4残留分支(期望404)', '/projects/%s/branches/br-withered-cake-w2hwfe53' % PA)
req('snapshots(期望空)', '/projects/%s/snapshots' % PA)
req('functions 列表', '/projects/%s/functions' % PA)
req('buckets 列表', '/projects/%s/buckets' % PA)
req('A 分支列表', '/projects/%s/branches' % PA)
