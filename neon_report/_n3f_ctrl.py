# -*- coding: utf-8 -*-
"""控制变量:无 X-Bug-Bounty header 的 create+presign(kb3)——复刻 _n3 成功路径"""
import http.client, ssl, json, sys, time
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
from _neon_creds_stage import API_HOST, API_BASE
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'
BUCKET = 'kb3'

def req(method, path, body=None):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status; conn.close()
    return st, raw

st, raw = req('POST', '/projects/%s/branches/%s/buckets' % (P, B), {'name': BUCKET})
print('create kb3 -> %d | %s' % (st, raw.decode(errors='replace')[:200]))
for i in range(3):
    st, raw = req('POST', '%s/projects/%s/branches/%s/buckets/%s/objects/o1.txt/presign' % (API_BASE, P, B, BUCKET),
                  {'operation': 'upload', 'content_type': 'text/plain'})
    print('presign kb3 try%d -> %d | %s' % (i, st, raw.decode(errors='replace')[:200]))
    if st == 200:
        break
    time.sleep(5)
# 同时测已存在的 kb1(曾成功过的 bucket)
st, raw = req('POST', '%s/projects/%s/branches/%s/buckets/kb1/objects/o1.txt/presign' % (API_BASE, P, B),
              {'operation': 'upload', 'content_type': 'text/plain'})
print('presign kb1(existing) -> %d | %s' % (st, raw.decode(errors='replace')[:200]))
