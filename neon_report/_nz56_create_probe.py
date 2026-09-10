# -*- coding: utf-8 -*-
"""H1-b: create project 参数位置定位 (query+body+header 组合, <=3 req)"""
import http.client, ssl, json, time, sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
OID = 'org-flat-dawn-91601224'
ctx = ssl.create_default_context()
R = uuid.uuid4().hex[:6]

def req(tag, path, body=None, extra_h=None):
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            if extra_h:
                h.update(extra_h)
            c.request('POST', API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = c.getresponse(); raw = r.read(); c.close()
            print('== %-24s -> %d  %s' % (tag, r.status, raw[:400].decode('utf-8', 'replace')))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

# 1) query + body 全带
req('query+body 全带', '/projects?org_id=%s' % OID,
    {'project': {'name': 'sbx-tr1-%s' % R, 'region_id': 'aws-us-east-2', 'pg_version': 18},
     'org_id': OID})

# 2) header X-Org-Id 变体
req('header X-Org-Id', '/projects',
    {'project': {'name': 'sbx-tr1-%s' % R}}, {'X-Org-Id': OID})
