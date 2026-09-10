# -*- coding: utf-8 -*-
"""H1-a: 创建 dummy 项目 + transfer_requests create 探测 (创建/状态观察, 可逆)"""
import http.client, ssl, json, time, sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
OID = 'org-flat-dawn-91601224'
ctx = ssl.create_default_context()
R = uuid.uuid4().hex[:6]

def req(tag, path, body=None, method=None):
    m = method or ('POST' if body is not None else 'GET')
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request(m, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = c.getresponse(); raw = r.read(); c.close()
            print('== %-28s -> %d  %s' % (tag, r.status, raw[:500].decode('utf-8', 'replace')))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

# 1) 创建 dummy 项目
st, raw = req('创建 dummy 项目', '/projects',
              {'project': {'name': 'sbx-tr1-%s' % R, 'region_id': 'aws-us-east-2', 'pg_version': 18}})
DP = None
try:
    d = json.loads(raw)
    DP = d.get('project', {}).get('id')
    print('   dummy project =', DP)
except Exception:
    pass

# 2) transfer create 空 body -> 看必填提示
if DP:
    req('transfer create 空body', '/projects/%s/transfer_requests' % DP, {})

# 3) transfer create 带 ttl=60
if DP:
    req('transfer create ttl=60', '/projects/%s/transfer_requests' % DP, {'ttl_seconds': 60})

# 4) 项目状态变化观察
if DP:
    req('项目状态', '/projects/%s' % DP)
    print('DP = %s (保留给下一步)' % DP)
