# -*- coding: utf-8 -*-
"""fuzz transaction action 的 queries 结构(serde untagged enum)
目标:1) 找到合法元素结构 2) 若成功,测多语句/分类器逐条语义
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()


def dbq(body, timeout=45):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    try:
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br':
            raw = brotli.decompress(raw)
        elif enc == 'gzip':
            raw = gzip.decompress(raw)
        st, out = r.status, raw[:500].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'EXC %r' % e
    finally:
        conn.close()
    return st, out


def t(label, queries, trunc=300):
    body = {'siteId': SITE_A, 'action': 'transaction', 'queries': queries}
    st, out = dbq(body)
    print('%-46s [%d] %s' % (label, st, out.replace('\n', ' | ')[:trunc]))


# 变体 1:字符串数组(已知失败,基线)
t('V1 [str]', ['select 1'])
# 变体 2-8:对象字段猜测
t('V2 [{sql}]', [{'sql': 'select 1'}])
t('V3 [{sql,params}]', [{'sql': 'select 1', 'params': []}])
t('V4 [{query}]', [{'query': 'select 1'}])
t('V5 [{statement}]', [{'statement': 'select 1'}])
t('V6 [{text,values}]', [{'text': 'select 1', 'values': []}])
t('V7 [{sql,params:[42]}]', [{'sql': 'select $1::int', 'params': [42]}])
t('V8 [{name,sql,params}]', [{'name': 'q1', 'sql': 'select 1', 'params': []}])
# 变体 9:queries 直接是字符串
t('V9 queries=str', 'select 1')
# 变体 10:两层数组
t('V10 [[obj]]', [[{'sql': 'select 1'}]])
# 变体 11:对象带语句+参数常见组合
t('V11 [{statement,args}]', [{'statement': 'select 1', 'args': []}])
