# -*- coding: utf-8 -*-
"""h1x44: Subscription 字段参数 + Mutation 字段名(匿名 introspection 部分)
Subscription: report_intent/llm_conversation_messages/conversation 的参数形状"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

q = '{ __type(name: "Subscription") { fields { name args { name type { kind name ofType { kind name } } } type { kind name ofType { name } } } } }'
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
print('Subscription:', r.text[:1500])
print()

q2 = '{ __type(name: "ReportIntentSubscriptionPayload") { fields { name type { kind name ofType { name } } } } }'
r2 = s.post('https://hackerone.com/graphql', json={'query': q2}, timeout=20)
print('Payload:', r2.text[:800])
