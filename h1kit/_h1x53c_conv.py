# -*- coding: utf-8 -*-
"""h1x53c: ReportAssistantConversation 字段 + conversation(id) 参数 + 与 intent 的关联(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=3000):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:cut].replace('\n', ' '))
    print()

for tn in ['ReportAssistantConversation', 'ReportAssistantConversationEntry', 'AtlassianAgentConversation']:
    probe('type_' + tn, '''query { __type(name: "%s") { kind fields { name type { kind name ofType { kind name } } } } }''' % tn)
# conversation 参数 + HaiChat 创建 mutation 形态
probe('conv_args', '''query { __type(name: "Query") { fields { name args { name type { kind name ofType { kind name ofType { kind name } } } } } } }''', 1200)
