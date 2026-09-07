# -*- coding: utf-8 -*-
"""OAS: 拉 console-stage openapi spec, 提取 snapshots 相关 schema (1 req)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()

for path in ['/openapi.json', '/api/v2/openapi.json', '/api/v2/docs']:
    try:
        c = http.client.HTTPSConnection(API_HOST, timeout=15, context=ctx)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
        h.update(HEADERS_TEST)
        c.request('GET', path, headers=h)
        r = c.getresponse(); raw = r.read(); c.close()
        print('== %s -> %d (%d B)' % (path, r.status, len(raw)))
        if r.status == 200 and len(raw) > 1000:
            try:
                d = json.loads(raw)
                fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_nz50_openapi.json')
                open(fn, 'w', encoding='utf-8').write(raw.decode('utf-8'))
                print('   已存', fn)
            except Exception as e:
                print('   parse err', e)
            break
        elif r.status == 200:
            print('   ', raw[:300])
    except Exception as e:
        print('[retry]', path, e); time.sleep(1)
