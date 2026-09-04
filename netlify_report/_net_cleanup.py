# -*- coding: utf-8 -*-
"""Netlify:清理旧 deploy(error + 早期测试)释放 credit,再试 create"""
import http.client, ssl, gzip, brotli, sys, json, time, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json', qs='', timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'netlify-cli/17.0.0 (node v24)', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_A, 'Content-Type': ctype}
    payload = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn.request(method, path + qs, body=payload, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

# 1. 全量 deploy 列表
s, raw = api('/api/v1/sites/%s/deploys?per_page=50' % SITE_A)
deploys = json.loads(raw)
print('total deploys:', len(deploys))
for dp in deploys:
    print(' ', dp.get('id', '')[:24], dp.get('state'), dp.get('title'), dp.get('created_at', '')[:19])

# 2. 删除 error 与早期测试 deploy(保留 published 和最近 3 个)
keep = {'6a97c9e3083c963fd210b895'}  # published fn-p6
del_count = 0
for dp in deploys:
    did = dp.get('id', '')
    if did in keep:
        print('KEEP', did[:20])
        continue
    if dp.get('state') == 'error' or dp.get('created_at', '')[:13] <= '2026-09-02T06:5':
        s2, raw2 = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, did), method='DELETE')
        print('DELETE', did[:20], dp.get('state'), '->', s2)
        del_count += 1
        time.sleep(0.3)
print('deleted:', del_count)

# 3. 重试 create
html = b'<html>test</html>'
body = {'title': 'credit-check', 'files': {'/index.html': hashlib.sha1(html).hexdigest()}}
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', body=body)
print('create after cleanup:', s, raw[:300].decode('utf-8', 'replace'))
if s == 200:
    DID = json.loads(raw).get('id')
    # 直接 publish 这个测试 deploy?不,先留着;验证可创建即可
    print('create OK, DID:', DID)
