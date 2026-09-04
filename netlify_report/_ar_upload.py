# -*- coding: utf-8 -*-
"""Agent Runner 文件上传交叉 + status:
1. POST /api/agent-runner-file-upload(自己 accountId 基线)
2. 交叉:B accountId(A cookie)
3. GET /api/agent-runners/status
用后即清(若成功上传,用返回 fileKey 删除)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B

TEAM_A = '6a979dd2ae93f47d55b62897'
TEAM_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()


def req(method, path, body=None, ct=None, cookie=COOKIE_A):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Cookie': cookie}
    if ct:
        h['Content-Type'] = ct
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:600].decode('utf-8', 'ignore')
    conn.close()
    return st, out


print('== status ==')
st, out = req('GET', '/api/agent-runners/status')
print('status        [%d] %s' % (st, out[:300]))
print()

print('== upload 小测试文件(1 字节,内容 "x") ==')
body = b'x'
for label, acc in [('self A', TEAM_A), ('cross B', TEAM_B)]:
    st, out = req('POST', '/api/agent-runner-file-upload?accountId=%s&filename=zz-test-%s.txt' % (acc, 'A' if acc == TEAM_A else 'B'),
                  body=body, ct='text/plain')
    print('%-10s [%d] %s' % (label, st, out[:400]))
