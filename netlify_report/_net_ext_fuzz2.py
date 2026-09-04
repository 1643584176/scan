# -*- coding: utf-8 -*-
"""extension-proxy:uuid 修正版 + 安装扩展流程挖取"""
import http.client, ssl, gzip, brotli, json, sys, time, re, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B, SITE_A

ACC_A = '6a979dd2ae93f47d55b62897'  # ajs_group_id A
ACC_B = '6a97b6454fef0db964f75db6'  # ajs_group_id B
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()

def req(path, cookie=COOKIE_A, method='GET', body=None, headers=None, timeout=20):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
    if headers: h.update(headers)
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = body if isinstance(body, bytes) else body.encode()
    t0 = time.time()
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    dt = time.time() - t0
    st = r.status
    b = raw.decode('utf-8', 'ignore').replace('\n', ' ')[:250]
    conn.close()
    return st, dt, b

def show(label, path, ck=COOKIE_A, hdrs=None, method='GET', body=None):
    st, dt, b = req(path, ck, method=method, body=body, headers=hdrs)
    print('%-42s %s %5.1fs | %s' % (label, st, dt, b))

print('==== 1. uuid 修正:extension-proxy ====')
show('ACC_A + A site', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (ACC_A, SITE_A))
show('ACC_A + B site', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (ACC_A, SITE_B))
show('ACC_B + A site', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (ACC_B, SITE_A), COOKIE_B)
show('ACC_B + fake', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (ACC_B, 'f' * 32), COOKIE_B)

print()
print('==== 2. fetch-extensions uuid 修正 ====')
show('list v=public ACC_A', '/.netlify/functions/fetch-extensions?teamId=%s&visibility=public' % ACC_A, hdrs={'Api-Version': '2'})
show('list v=installed ACC_A', '/.netlify/functions/fetch-extensions?teamId=%s&visibility=installed' % ACC_A, hdrs={'Api-Version': '2'})
show('list no v ACC_A', '/.netlify/functions/fetch-extensions?teamId=%s' % ACC_A, hdrs={'Api-Version': '2'})

print()
print('==== 3. fetch-extension uuid 修正 ====')
show('fetch-ext ACC_A slug=abc', '/.netlify/functions/fetch-extension?slug=abc&teamId=%s' % ACC_A, hdrs={'Api-Version': '2'})

print()
print('==== 4. manage-extension-proxy 请求体挖取 ====')
data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()
# 找所有 manage-extension-proxy 出现的较宽上下文,找 fetch/body 构造
seen = set()
for m in re.finditer('manage-extension-proxy', data):
    s = max(0, m.start() - 200)
    e = min(len(data), m.end() + 1200)
    seg = data[s:e]
    if seg in seen:
        continue
    seen.add(seg)
    if 'fetch' in seg[e - 1200:] or 'method' in seg or 'body' in seg:
        print('--- hit @%d ---' % m.start())
        print(seg.replace('\n', ' ')[:1300])
        print('=' * 50)
    if len(seen) > 6:
        break
# 搜 install 动词
for key in ['installIntegration', 'install-extension', 'extension/install', 'installedOnTeam']:
    for m in list(re.finditer(re.escape(key), data))[:1]:
        s = max(0, m.start() - 400)
        e = min(len(data), m.end() + 700)
        print('--- key %s @%d ---' % (key, m.start()))
        print(data[s:e].replace('\n', ' ')[:1000])
        print('=' * 50)
print('done')
