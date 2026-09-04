# -*- coding: utf-8 -*-
"""1) api.neon.tech 连接错误详情 2) neon.com docs 页找 OpenAPI 链接"""
import http.client, ssl, re

ctx = ssl.create_default_context()

# 1. api.neon.tech 错误详情
try:
    conn = http.client.HTTPSConnection('api.neon.tech', context=ctx, timeout=15)
    conn.request('GET', '/openapi.json', headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
    r = conn.getresponse()
    print('api.neon.tech st:', r.status)
    print(r.read()[:300])
    conn.close()
except Exception as e:
    print('api.neon.tech EXC:', repr(e)[:300])

# 2. neon.com docs 页抓 openapi 链接
try:
    conn = http.client.HTTPSConnection('neon.com', context=ctx, timeout=30)
    conn.request('GET', '/docs/reference/api', headers={'User-Agent': 'Mozilla/5.0'})
    r = conn.getresponse(); raw = r.read(); conn.close()
    print('docs len:', len(raw))
    txt = raw.decode('utf-8', 'replace')
    # 找 openapi/spec/swagger/yaml/json 下载链接
    for pat in [r'https?://[^"\'\s<>]+?openapi[^"\'\s<>]*', r'https?://[^"\'\s<>]+?\.(?:yaml|yml|json)[^"\'\s<>]*']:
        ms = set(re.findall(pat, txt))
        for m in sorted(ms)[:20]:
            print('LINK:', m[:160])
    # 找 "specification"/"download" 上下文
    for kw in ['openapi', 'OpenAPI', 'specification', 'download']:
        idxs = [mm.start() for mm in re.finditer(kw, txt)][:5]
        for i in idxs:
            print('CTX[%s]:' % kw, txt[max(0,i-120):i+160].replace('\n', ' ')[:280])
except Exception as e:
    print('docs EXC:', repr(e)[:300])
