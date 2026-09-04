# -*- coding: utf-8 -*-
"""重建 bucket(全新名 kb2)+ presign 输出 URL——带等待与重试"""
import http.client, ssl, json, sys, time
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'
BUCKET = 'kb2'

def req(method, path, body=None):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status; conn.close()
    return st, raw

st, raw = req('POST', '/projects/%s/branches/%s/buckets' % (P, B), {'name': BUCKET})
print('create %s -> %d | %s' % (BUCKET, st, raw.decode(errors='replace')[:200]))
time.sleep(3)
ok = False
for i in range(4):
    st, raw = req('POST', '%s/projects/%s/branches/%s/buckets/%s/objects/o1.txt/presign' % (API_BASE, P, B, BUCKET),
                  {'operation': 'upload', 'content_type': 'text/plain'})
    print('presign try%d -> %d | %s' % (i, st, raw.decode(errors='replace')[:250]))
    if st == 200:
        ok = True
        break
    time.sleep(4)
if ok:
    pr = json.loads(raw)
    open(r'D:\scan\neon_report\_presign_url.txt', 'w').write(pr['url'])
    open(r'D:\scan\neon_report\_presign_hdrs.txt', 'w').write(json.dumps(pr.get('headers', {})))
    print('URL saved (%d chars)' % len(pr['url']))
