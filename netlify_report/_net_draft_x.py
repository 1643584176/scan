# -*- coding: utf-8 -*-
"""draft deploy 状态机推进 + 文件上传 + 匿名/B 读取测试(未发布内容泄露候选)"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'

def req(method, path, body=None, token=TOKEN_A, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if body is not None:
        h['Content-Type'] = 'application/json'
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

def probe(tag, m, p, body=None, tok=TOKEN_A):
    st, b = req(m, p, body, tok)
    print('%-60s %s | %s' % (tag, st, b[:200].replace('\n', ' ')))
    return st, b

print('== 1. 创建 draft deploy ==')
st, b = req('POST', '/api/v1/sites/%s/deploys' % SITE_A, {'draft': True})
print(st, b[:200])
did = json.loads(b).get('id')
print('draft id:', did)

print()
print('== 2. 状态机推进尝试 ==')
for m, body in [
    ('PUT', {'state': 'uploading'}),
    ('POST', {'state': 'uploading'}),
    ('PUT', {'async': True}),
]:
    st, b = req(m, '/api/v1/deploys/%s' % did, body)
    print('%-5s %s | %s' % (m, st, b[:180].replace('\n', ' ')))

print()
print('== 3. PUT files 试传 ==')
st, b = req('PUT', '/api/v1/deploys/%s/files/index.html' % did,
            b'<html>SECRET-DRAFT-CONTENT-zz</html>')
print('PUT file:', st, b[:200])

print()
print('== 4. 状态查看 ==')
st, b = req('GET', '/api/v1/deploys/%s' % did)
print('GET deploy:', st, b[:300])
st, b = req('GET', '/api/v1/deploys/%s/files' % did)
print('GET files list:', st, b[:300])

print()
print('== 5. 读取测试: 文件内容(owner / B / 匿名)==')
fp = '/api/v1/deploys/%s/files/index.html' % did
for tag, tok in [('A owner', TOKEN_A), ('B cross', TOKEN_B), ('匿名', None)]:
    st, b = req('GET', fp, token=tok)
    print('%-10s %s | %s' % (tag, st, b[:200].replace('\n', ' ')))

print()
print('== 6. 直接 URL 访问 draft ==')
st, b = req('GET', '/', None, None, host='%s--sec-test-rcf6lz.netlify.app' % did)
print('draft url GET:', st, b[:150])
print('done')
