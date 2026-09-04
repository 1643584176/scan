# -*- coding: utf-8 -*-
"""本地探测 lambda-events.services.netlify.com(确认是否公网可达 + POST 路径枚举)"""
import http.client, ssl, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')

ctx = ssl.create_default_context()
NF_TOKEN = '062d3d30-a9b9-4477-aa69-4a3dba0d5b30'  # 从函数 env 中观察到的值

def req(method, path, body=None, headers=None, host='lambda-events.services.netlify.com'):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
        if headers:
            h.update(headers)
        payload = body.encode() if isinstance(body, str) else body
        conn.request(method, path, body=payload, headers=h)
        r = conn.getresponse()
        raw = r.read()
        ct = r.getheader('Content-Type', '')
        st = r.status
        conn.close()
        return st, raw[:400].decode('utf-8', 'replace').replace('\n', ' ')
    except Exception as e:
        return 'ERR', str(e)[:150]

# 1. 基础探测
print('== GET /health:', req('GET', '/health'))
print('== GET /:', req('GET', '/'))

# 2. POST 常见路径
paths = ['/', '/v1/events', '/events', '/api/v1/events', '/v1/traces', '/traces', '/ingest', '/v1/ingest',
         '/api/events', '/v1/telemetry', '/telemetry', '/v1/logs', '/logs', '/lambda-events', '/v1/lambda-events',
         '/record', '/v1/record', '/dispatch', '/v1/dispatch', '/api/v1/telemetry', '/v1/span', '/spans']
for p in paths:
    st, body = req('POST', p, body='{}', headers={'Content-Type': 'application/json'})
    print('POST %-24s -> %s %s' % (p, st, body[:150]))

# 3. 带 token 头 POST
for hdr_name in ['x-api-key', 'Authorization', 'X-NF-Token', 'NETLIFY-FUNCTIONS-TOKEN']:
    st, body = req('POST', '/v1/events', body='{}',
                   headers={'Content-Type': 'application/json', hdr_name: NF_TOKEN})
    print('POST /v1/events [%s] -> %s %s' % (hdr_name, st, body[:150]))
