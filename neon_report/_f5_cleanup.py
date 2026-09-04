# -*- coding: utf-8 -*-
"""清理 kf1 function + 检查全残留(kb/buckets/credentials/functions/branches)"""
import http.client, ssl, json, sys
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'

def req(method, path, body=None):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status; conn.close()
    return st, raw

# 1. 删 kf1 function
st, raw = req('DELETE', '/projects/%s/branches/%s/functions/kf1' % (P, B))
print('delete kf1 -> %d' % st)

# 2. 残留检查
st, raw = req('GET', '/projects/%s/branches/%s/buckets' % (P, B))
print('buckets -> %d | %s' % (st, raw.decode(errors='replace')[:300]))
st, raw = req('GET', '/projects/%s/branches/%s/functions' % (P, B))
print('functions -> %d | %s' % (st, raw.decode(errors='replace')[:300]))
st, raw = req('GET', '/projects/%s/branches/%s/credentials' % (P, B))
print('credentials -> %d | %s' % (st, raw.decode(errors='replace')[:600]))
st, raw = req('GET', '/projects/%s/branches' % P)
try:
    brs = json.loads(raw).get('branches', [])
    print('branches:', [(b['id'], b['name']) for b in brs])
except Exception as e:
    print('branches parse err', e)
