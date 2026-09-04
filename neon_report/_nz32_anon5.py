# -*- coding: utf-8 -*-
"""br5: 控制面 masking_function=concat(current_user::text) -> 平台作业执行上下文验证"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'

def req(tag, path, body=None, method=None):
    m = method or ('POST' if body is not None else 'GET')
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request(m, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = c.getresponse(); raw = r.read()
            c.close()
            print('\n== %s -> %d' % (tag, r.status))
            print(raw[:600].decode('utf-8', errors='replace'))
            return r.status, raw
        except Exception as e:
            print('[retry %s]' % tag, e); time.sleep(2)
    return None, None

body = {
    'branch': {'name': 'sbx-anon-t5'},
    'masking_rules': [{
        'database_name': 'neondb', 'schema_name': 'public',
        'table_name': 'sbx_anon_src', 'column_name': 'email',
        'masking_function': 'pg_catalog.concat(current_user::text)'
    }],
    'start_anonymization': True,
}
st, raw = req('create', '/projects/%s/branch_anonymized' % P, body)
BR5 = None
try:
    BR5 = json.loads(raw).get('branch', {}).get('id')
    print('BR5 =', BR5)
except Exception:
    pass
if BR5:
    for i in range(15):
        time.sleep(5)
        st2, raw2 = req('poll%d' % i, '/projects/%s/branches/%s/anonymized_status' % (P, BR5), method='GET')
        try:
            d = json.loads(raw2)
            print('   state:', d.get('state'), '|', str(d.get('status_message', ''))[:160])
            if d.get('state') in ('anonymized', 'error', 'failed'):
                if d.get('last_run'):
                    print('   last_run:', json.dumps(d.get('last_run'), ensure_ascii=False)[:400])
                break
        except Exception:
            pass
