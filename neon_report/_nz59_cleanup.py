# -*- coding: utf-8 -*-
"""清理: 删除 09-05 遗留分支 br-raspy-snow-w2n12fvw + 确认 (2 req)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
ctx = ssl.create_default_context()

def req(tag, path, method='GET'):
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request(method, API_BASE + path, headers=h)
            r = c.getresponse(); raw = r.read(); c.close()
            print('== %-28s -> %d  %s' % (tag, r.status, raw[:200].decode('utf-8', 'replace')))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

req('DELETE raspy-snow', '/projects/%s/branches/br-raspy-snow-w2n12fvw' % PA, method='DELETE')
time.sleep(3)
req('分支列表确认', '/projects/%s/branches' % PA)
