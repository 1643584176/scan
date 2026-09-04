# -*- coding: utf-8 -*-
"""公开侦察3: dashboard chunk 下载策略
1. buildManifest.js -> 路由->chunk 映射
2. 挑 database/sql/settings 相关页面 chunk 下载
"""
import http.client, ssl, re, os, json

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))
ASSET = 'frontend-assets.supabase.com'
BUILD = 'e25c0e83dff6/_next/static/build-TfctsWXpff2fKS'

def get(path, maxlen=None):
    conn = http.client.HTTPSConnection(ASSET, context=ctx, timeout=30)
    conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0'})
    r = conn.getresponse()
    raw = r.read(maxlen) if maxlen else r.read()
    conn.close()
    return r.status, raw

# 1. buildManifest
st, raw = get('/studio/%s/_buildManifest.js?dpl=dpl_GLqRDMh84dxi3VMQSqnbyNXiXA6A' % BUILD)
print('buildManifest:', st, len(raw), flush=True)
if st == 200:
    txt = raw.decode('utf-8', 'ignore')
    fn = os.path.join(here, '_sb05_buildManifest.js')
    open(fn, 'w', encoding='utf-8').write(txt)
    # 提取路由->chunks
    m = re.search(r'self\.__BUILD_MANIFEST\s*=\s*(\{.*?\})\s*;?\s*self\.__BUILD_MANIFEST_CB', txt, re.S)
    if not m:
        m = re.search(r'__BUILD_MANIFEST\s*=\s*(\{.*)$', txt, re.S)
    # 找 sql/database 相关路由
    routes = set(re.findall(r'"([^"]{0,80}(?:sql|database|pg-meta|supautils|functions|storage|settings)[^"]{0,80})"\s*:', txt, re.I))
    print('related route keys (%d):' % len(routes), flush=True)
    for rt in sorted(routes)[:60]:
        print('  ', rt, flush=True)
