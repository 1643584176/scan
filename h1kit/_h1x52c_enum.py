# -*- coding: utf-8 -*-
"""h1x52c: search index 参数类型枚举 + conversation union 成员 + analytics 枚举参数(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, query):
    r = s.post('https://hackerone.com/graphql', json={'query': query}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:3000])
    print()

# 1. search 参数类型(找 index 的枚举类型名)
probe('search_arg_types', '''query { __type(name: "Query") { fields { name args { name type { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } } }''')

# 2. ConversationUnion 成员
probe('conversation_union', '''query { __type(name: "ConversationUnion") { kind name possibleTypes { name } } }''')
# 3. DocumentUnion 成员(回顾)
probe('document_union', '''query { __type(name: "DocumentUnion") { kind name possibleTypes { name } } }''')
