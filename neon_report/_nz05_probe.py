# -*- coding: utf-8 -*-
"""未测面 GET 探测轮 (全部自己的项目A, ≤10rps, X-Bug-Bounty)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'

def req(tag, path, body=None):
    for attempt in range(2):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request('POST' if body is not None else 'GET', API_BASE + path,
                      body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = c.getresponse(); raw = r.read()
            c.close()
            print('\n== %s -> %d' % (tag, r.status))
            try:
                print(json.dumps(json.loads(raw), indent=1, ensure_ascii=False)[:800])
            except Exception:
                print(raw[:200])
            return
        except Exception as e:
            print('[retry %s] %s' % (tag, e)); time.sleep(2)
    print('\n== %s -> FAIL' % tag)

req('projects/shared', '/projects/shared')
req('permissions', '/projects/%s/permissions' % P)
req('members', '/projects/%s/members' % P)
req('advisors', '/projects/%s/advisors' % P)
req('masking_rules', '/projects/%s/branches/%s/masking_rules' % (P, B))
req('anonymized_status', '/projects/%s/branches/%s/anonymized_status' % (P, B))
req('backup_schedule', '/projects/%s/branches/%s/backup_schedule' % (P, B))
req('schema', '/projects/%s/branches/%s/schema' % (P, B))
req('connection_uri', '/projects/%s/connection_uri' % P)
req('operations', '/projects/%s/operations?limit=5' % P)
req('org_vpc', '/organizations/org-flat-dawn-91601224/vpc/region/us-east-2/vpc_endpoints')
req('me', '/users/me')
