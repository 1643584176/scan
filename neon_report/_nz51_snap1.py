# -*- coding: utf-8 -*-
"""T5a: create snapshot on A main (expires_at=+2h 自动清) + list (2 req)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
MAIN = 'br-wandering-field-w2ob6mpn'
ctx = ssl.create_default_context()

def req(tag, path, body=None, method=None):
    m = method or ('POST' if body is not None else 'GET')
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request(m, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = c.getresponse(); raw = r.read(); c.close()
            print('== %-30s -> %d  %s' % (tag, r.status, raw[:500].decode('utf-8', 'replace')))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

# create snapshot: expires_at = now + 2h
exp = int(time.time() * 1000) + 7200000
st, raw = req('create snapshot', '/projects/%s/branches/%s/snapshot' % (PA, MAIN),
              {'expires_at': exp})
SID = None
try:
    d = json.loads(raw)
    print('   keys:', list(d.keys()))
    sn = d.get('snapshot', d)
    SID = sn.get('id')
    print('   snapshot_id =', SID, '| source_branch_id =', sn.get('source_branch_id'),
          '| expires_at =', sn.get('expires_at'), '| status =', sn.get('status'))
except Exception as e:
    print('   parse err', e)

# list
req('list snapshots', '/projects/%s/snapshots' % PA)
