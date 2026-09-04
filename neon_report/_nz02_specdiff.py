# -*- coding: utf-8 -*-
"""拉取 staging 最新 OpenAPI spec 并 diff 09-03 版"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']

ctx = ssl.create_default_context()
paths_try = ['/api/v2/openapi.json', '/openapi.json', '/api/v2/spec.json', '/api/v2/docs/openapi.json']
old = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
old_paths = set(old.get('paths', {}).keys())
old_total = len(old_paths)

for p in paths_try:
    try:
        c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Authorization': 'Bearer ' + key}
        h.update(HEADERS_TEST)
        c.request('GET', p, headers=h)
        r = c.getresponse()
        b = r.read(2000000)
        c.close()
        print('[%s] %d len=%d' % (p, r.status, len(b)))
        if r.status == 200 and len(b) > 10000:
            spec = json.loads(b.decode('utf-8'))
            new_paths = set(spec.get('paths', {}).keys())
            print('old_total=%d new_total=%d' % (old_total, len(new_paths)))
            added = sorted(new_paths - old_paths)
            removed = sorted(old_paths - new_paths)
            print('=== ADDED %d ===' % len(added))
            for x in added:
                methods = ','.join(m.upper() for m in spec['paths'][x] if m in ('get', 'post', 'patch', 'put', 'delete'))
                print('  %-70s %s' % (x, methods))
            print('=== REMOVED %d ===' % len(removed))
            for x in removed[:30]:
                print('  ', x)
            # 保存新 spec
            open(r'D:\scan\neon_report\_openapi_v2_new.json', 'w', encoding='utf-8').write(
                json.dumps(spec, ensure_ascii=False, indent=1))
            print('saved _openapi_v2_new.json')
            break
    except Exception as e:
        print('[%s] ERR %s' % (p, e))
