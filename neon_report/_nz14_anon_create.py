# -*- coding: utf-8 -*-
"""POST branch_anonymized 试探: 最小 body -> 错误提示找必填字段"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'

def post(tag, path, body):
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request('POST', API_BASE + path, body=json.dumps(body).encode(), headers=h)
            r = c.getresponse(); raw = r.read()
            c.close()
            print('\n== %s -> %d' % (tag, r.status))
            print(raw[:1500].decode('utf-8', errors='replace'))
            return r.status, raw
        except Exception as e:
            print('[retry]', e); time.sleep(2)
    return None, None

# 1) 空 body
post('empty', '/projects/%s/branch_anonymized' % P, {})
time.sleep(2)
# 2) 带常见字段
post('named', '/projects/%s/branch_anonymized' % P, {
    'branch': {'name': 'sbx-anon-t1'},
    'masking_rules': [{
        'database_name': 'neondb', 'schema_name': 'public',
        'table_name': 'sbx_anon_src', 'column_name': 'email',
        'masking_function': 'anon.fake_email()'
    }],
    'start_anonymization': False,
})
