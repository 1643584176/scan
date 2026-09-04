# -*- coding: utf-8 -*-
"""Beta 面可用性探测(buckets/functions/credentials/auth-webhooks/custom-domains/backup/snapshot)
全部 GET 只读,零破坏。判断哪些新功能面在 staging 可用 → 决定下一轮测试方向"""
import http.client, ssl, json, sys
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']

P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'

def req(method, path, body=None):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
        h.update(HEADERS_TEST)
        conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status; conn.close()
        return st, raw[:600]
    except Exception as e:
        return 0, str(e).encode()[:300]

tests = [
    ('bucket list', 'GET', '/projects/%s/branches/%s/buckets' % (P, B)),
    ('functions list', 'GET', '/projects/%s/branches/%s/functions' % (P, B)),
    ('credentials list', 'GET', '/projects/%s/branches/%s/credentials' % (P, B)),
    ('auth webhooks cfg', 'GET', '/projects/%s/branches/%s/auth/webhooks' % (P, B)),
    ('auth domains', 'GET', '/projects/%s/branches/%s/auth/domains' % (P, B)),
    ('custom-domains', 'GET', '/projects/%s/branches/%s/custom-domains' % (P, B)),
    ('data-api cfg(base)', 'GET', '/projects/%s/branches/%s/data-api/neondb' % (P, B)),
    ('backup_schedule', 'GET', '/projects/%s/branches/%s/backup_schedule' % (P, B)),
    ('snapshots', 'GET', '/projects/%s/snapshots' % P),
    ('branches', 'GET', '/projects/%s/branches' % P),
]
for tag, m, path in tests:
    st, raw = req(m, path)
    print('\n== %s -> %d' % (tag, st))
    print('  ', raw.decode(errors='replace')[:400])
