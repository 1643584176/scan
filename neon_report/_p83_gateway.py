# -*- coding: utf-8 -*-
"""1. bat 内 generateOAuthToken/generateDatabaseCredential 方法体(path/method)
2. AI gateway 数据面无凭据探测(只读)
"""
import re, os, sys, http.client, ssl, json

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
i_bat = src.find('class bat extends yat')
i_kde = src.find('const Kde')
seg = src[i_bat:i_kde]

out = []
for kw in ['generateOAuthToken', 'generateDatabaseCredential', 'getProjectBranchAiGateway',
           'listAiGatewayModels', 'resolveAiGatewayIdentity', 'purchaseAigwCredits']:
    i = seg.find(kw)
    if i >= 0:
        out.append('KW %s @bat+%d: %s' % (kw, i, seg[max(0, i - 80):i + 420].replace('\n', ' ')[:480]))
    else:
        out.append('KW %s NOT in bat (call site only)' % kw)
open(os.path.join(here, '_p83_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)

# 2. 网关数据面
ctx = ssl.create_default_context()
GW = 'br-orange-flower-a57knkws-api.ai.c-1.us-east-2.aws.neon.tech'
res = []
for path in ['/', '/v1/models', '/healthz', '/v1/chat/completions', '/v1/projects']:
    try:
        conn = http.client.HTTPSConnection(GW, context=ctx, timeout=20)
        conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
        r = conn.getresponse()
        raw = r.read().decode('utf-8', 'ignore')
        res.append('GET %-24s %s [%s] %s' % (path, r.status, r.getheader('content-type', ''), raw[:400].replace('\n', ' ')))
        conn.close()
    except Exception as e:
        res.append('GET %s EXC %s' % (path, e))
open(os.path.join(here, '_p83_gw.txt'), 'w', encoding='utf-8').write('\n'.join(res))
print('\n'.join(res), flush=True)
