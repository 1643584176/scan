# -*- coding: utf-8 -*-
"""收尾验证: ①源分支数据未污染 ②br5 PATCH masking_rules 重触发 ③POST anonymize 重跑"""
import http.client, ssl, json, time, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
BR5 = 'br-snowy-wave-w2w54e8k'

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
            print(raw[:500].decode('utf-8', errors='replace'))
            return r.status, raw
        except Exception as e:
            print('[retry %s]' % tag, e); time.sleep(2)
    return None, None

def geturi(branch_id=None):
    p = '/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner' % P
    if branch_id:
        p += '&branch_id=' + branch_id
    st, raw = req('uri', p, method='GET')
    if not raw:
        return None
    try:
        uri = json.loads(raw).get('uri', '')
        parts = urllib.parse.urlsplit(uri)
        q = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if k != 'channel_binding']
        return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(q), parts.fragment))
    except Exception:
        return None

import urllib.parse, psycopg

# ① 源分支数据确认
uri0 = geturi()
with psycopg.connect(uri0, connect_timeout=20) as conn:
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute('select id, email, full_name from public.sbx_anon_src order by id')
    print('\n-- source branch data:')
    for row in cur.fetchall():
        print('  ', row)

# ② PATCH masking_rules (追加 full_name 列规则)
req('patch-rules', '/projects/%s/branches/%s/masking_rules' % (P, BR5), {
    'masking_rules': [
        {'database_name': 'neondb', 'schema_name': 'public', 'table_name': 'sbx_anon_src',
         'column_name': 'email', 'masking_function': 'pg_catalog.concat(current_user::text)'},
        {'database_name': 'neondb', 'schema_name': 'public', 'table_name': 'sbx_anon_src',
         'column_name': 'full_name', 'masking_function': 'anon.fake_last_name()'},
    ]
}, method='PATCH')
time.sleep(1)
# ③ POST anonymize 重跑 (之前 405, 再确认)
req('re-anonymize', '/projects/%s/branches/%s/anonymize' % (P, BR5), {}, method='POST')
time.sleep(2)
st, raw = req('status-after', '/projects/%s/branches/%s/anonymized_status' % (P, BR5), method='GET')
try:
    d = json.loads(raw)
    print('state:', d.get('state'), '|', str(d.get('status_message', ''))[:200])
except Exception:
    pass
# ④ 查 br5 数据是否被重脱敏
uri5 = geturi(BR5)
if uri5:
    try:
        with psycopg.connect(uri5, connect_timeout=20) as conn:
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute('select id, email, full_name from public.sbx_anon_src order by id')
            print('\n-- br5 data after patch:')
            for row in cur.fetchall():
                print('  ', row)
    except Exception as e:
        print('br5 conn err:', str(e)[:150])
