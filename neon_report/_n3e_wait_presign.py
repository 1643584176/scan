# -*- coding: utf-8 -*-
"""kb2 等待传播后 list + presign 重试;再验证 presign 路由本身"""
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

# list 确认 kb2 可见性
st, raw = req('GET', '/projects/%s/branches/%s/buckets' % (P, B))
print('list buckets -> %d | %s' % (st, raw.decode(errors='replace')[:300]))

# 等 60s 再 presign
print('waiting 60s for propagation...')
time.sleep(60)
for i in range(5):
    st, raw = req('POST', '%s/projects/%s/branches/%s/buckets/%s/objects/o1.txt/presign' % (API_BASE, P, B, BUCKET),
                  {'operation': 'upload', 'content_type': 'text/plain'})
    print('presign try%d -> %d | %s' % (i, st, raw.decode(errors='replace')[:250]))
    if st == 200:
        pr = json.loads(raw)
        open(r'D:\scan\neon_report\_presign_url.txt', 'w').write(pr['url'])
        open(r'D:\scan\neon_report\_presign_hdrs.txt', 'w').write(json.dumps(pr.get('headers', {})))
        print('URL saved (%d chars)' % len(pr['url']))
        break
    time.sleep(8)
