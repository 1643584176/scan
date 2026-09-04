# -*- coding: utf-8 -*-
"""下载 prod bundle app-CcBRprEu.js -> 对比本地 _js/app.js -> 搜 observability/so 定义/端点主机"""
import http.client, ssl, re, os, sys, hashlib

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

conn = http.client.HTTPSConnection('dfv3qgd2ykmrx.cloudfront.net', context=ctx, timeout=60)
conn.request('GET', '/assets/app-CcBRprEu.js', headers={'User-Agent': 'Mozilla/5.0'})
r = conn.getresponse()
raw = r.read()
conn.close()
print('download len:', len(raw), flush=True)
outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_js', 'prod_app.js')
open(outp, 'wb').write(raw)
print('sha256:', hashlib.sha256(raw).hexdigest()[:16], flush=True)

local = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_js', 'app.js'), 'rb').read()
print('local len:', len(local), 'sha256:', hashlib.sha256(local).hexdigest()[:16], flush=True)

src = raw.decode('utf-8', 'replace')
print('same file:', src == local.decode('utf-8', 'replace'), flush=True)

# 搜 observability 上下文中的主机/完整 URL
for kw in ['observability-settings', 'listObservabilityConfigurations']:
    i = src.find(kw)
    if i >= 0:
        seg = src[max(0, i - 1500):i + 500]
        # 找 http(s) 主机
        hosts = set(re.findall(r'https?://[a-zA-Z0-9._-]+', seg))
        print('KW', kw, 'nearby hosts:', hosts, flush=True)
        print(seg[:1200].replace('\n', ' '), flush=True)
