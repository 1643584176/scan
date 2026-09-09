# -*- coding: utf-8 -*-
"""h1x52r: 新候选根查询类型 introspect: resource/ReportRetestUser/HaiChat/ReportIntent/ConversationUnion 等"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=3500):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:cut].replace('\n', ' '))
    print()

# 1. ResourceInterface 成员 + Report 是否实现
probe('resource_union', '''query { __type(name: "ResourceInterface") { kind possibleTypes { name } fields { name type { kind name } } } }''')
# 2. ReportRetestUser 字段 + ReportRetest 类型
probe('retest_user', '''query { __type(name: "ReportRetestUser") { kind fields { name type { kind name ofType { kind name } } } } }''')
probe('retest_type', '''query { __type(name: "ReportRetest") { kind fields { name type { kind name ofType { kind name } } } } }''')
# 3. HaiChat / ReportIntent id 参数形态
probe('hai_chat', '''query { __type(name: "HaiChat") { kind fields { name type { kind name ofType { kind name } } } } }''')
probe('report_intent', '''query { __type(name: "ReportIntent") { kind fields { name type { kind name ofType { kind name } } } } }''')
# 4. ConversationUnion 成员
probe('conv_union', '''query { __type(name: "ConversationUnion") { kind possibleTypes { name } } }''')
