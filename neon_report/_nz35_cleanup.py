# -*- coding: utf-8 -*-
"""清理: 删 br1~br5 脱敏分支 + 源分支测试对象"""
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
            print('== %s -> %d | %s' % (tag, r.status, raw[:250].decode('utf-8', errors='replace')))
            return r.status, raw
        except Exception as e:
            print('[retry %s]' % tag, e); time.sleep(2)
    return None, None

# 1) 删脱敏分支 (先看 endpoint 列表再删)
for b, tag in (('br-late-lab-w2z537vl', 'br1'), ('br-proud-haze-w2hel016', 'br2'),
               ('br-rapid-lake-w2aky5fq', 'br3'), ('br-snowy-wave-w2w54e8k', 'br5')):
    st, raw = req('%s_del' % tag, '/projects/%s/branches/%s' % (P, b), method='DELETE')
    time.sleep(1)

# 2) 源分支删测试对象
def geturi():
    st, raw = req('uri', '/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner' % P, method='GET')
    uri = json.loads(raw).get('uri', '')
    import urllib.parse
    parts = urllib.parse.urlsplit(uri)
    q = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if k != 'channel_binding']
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(q), parts.fragment))

import psycopg
try:
    with psycopg.connect(geturi(), connect_timeout=20) as conn:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute('drop table if exists public.sbx_anon_src cascade')
        cur.execute('drop table if exists public.sbx_probe_log cascade')
        cur.execute('drop function if exists public.sbx_probe_fn() cascade')
        cur.execute('drop function if exists public.mk_fn() cascade')
        # 清 anon seclabel 残留
        try:
            cur.execute("select relname from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and relname like 'sbx_%'")
            print('remaining sbx objects:', cur.fetchall())
        except Exception as e:
            print('check err', e)
    print('source objects cleaned')
except Exception as e:
    print('DB ERR', e)

# 3) 分支列表确认
time.sleep(2)
req('branches-final', '/projects/%s/branches' % P, method='GET')
