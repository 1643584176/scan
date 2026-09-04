# -*- coding: utf-8 -*-
import http.client, ssl, os, re

ctx = ssl.create_default_context()

def get(host, path):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=30)
        conn.request('GET', path, headers={'Accept': 'application/json'})
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        conn.close()
        return st, raw[:120].decode('utf-8', 'replace')
    except Exception as e:
        return -1, str(e)[:80]

for fn in ['probe1', 'probe4', 'probe10']:
    s, b = get('sec-b-08v4pk.netlify.app', '/.netlify/functions/' + fn)
    print('B probe%-4s -> %d %s' % (fn, s, b.replace('\n', ' ')[:100]))

# _zisi/out2 函数 zip
z = r'D:\scan\netlify_report\_zisi\out2'
if os.path.isdir(z):
    print('zips:', sorted(os.listdir(z))[:15])

# 找 ssrf-matrix 相关 site 域名
base = r'D:\scan\netlify_report'
for f in sorted(os.listdir(base)):
    if not f.endswith('.py'):
        continue
    t = open(os.path.join(base, f), encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'https?://([a-z0-9-]+\.netlify\.app)', t):
        print(f, '->', m.group(1))
        break
