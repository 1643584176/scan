# -*- coding: utf-8 -*-
"""清理 t1 + 分析 verify/git 接口调用形态"""
import http.client, ssl, gzip, brotli, json, sys, re
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

ctx = ssl.create_default_context()

def q(sql):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Cookie': COOKIE_A, 'Content-Type': 'application/json'}
    body = json.dumps({'siteId': '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4', 'action': 'query', 'sql': sql}).encode()
    conn.request('POST', '/.netlify/functions/database-query', body=body, headers=h)
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

st, raw = q('drop table if exists t1')
print('drop t1:', st, raw[:80].decode('utf-8', 'ignore'))
st, raw = q("select table_name from information_schema.tables where table_schema='public'")
print('tables now:', raw.decode('utf-8', 'ignore')[:200])

# verify?domain= 调用形态
data = open(r'D:\scan\netlify_report\_js\net_actions.js', encoding='utf-8', errors='ignore').read()
for key in ['verify?domain', '/.netlify/functions/verify', '/.netlify/functions/git']:
    print('=' * 70)
    print('KEY:', key)
    cnt = 0
    for m in re.finditer(re.escape(key), data):
        s = max(0, m.start() - 500)
        e = min(len(data), m.end() + 500)
        print(data[s:e].replace('\n', ' '))
        print('-' * 60)
        cnt += 1
        if cnt >= 2:
            break
