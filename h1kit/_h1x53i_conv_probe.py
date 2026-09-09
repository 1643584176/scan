# -*- coding: utf-8 -*-
"""h1x53i: conversation(id) 正确语法重测 + ConversationInterface/Entry 字段 introspection"""
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=800):
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=15)
        print('%-42s [%s] %s' % (name, r.status_code, r.text[:cut].replace('\n', ' ')))
    except Exception as e:
        print('%-42s ERR %s' % (name, e))
    time.sleep(0.3)

F = '... on ConversationInterface { id type entries { nodes { id } } }'
probe('conv_1', '''query { conversation(id: "1") { %s } }''' % F)
probe('conv_3732660', '''query { conversation(id: "3732660") { %s } }''' % F)
probe('conv_gid_report', '''query { conversation(id: "gid://hackerone/Report/3732660") { %s } }''' % F)
probe('conv_gid_conv', '''query { conversation(id: "gid://hackerone/ReportAssistantConversation/1") { %s } }''' % F)
probe('conv_gid_conv3732660', '''query { conversation(id: "gid://hackerone/ReportAssistantConversation/3732660") { %s } }''' % F)

# introspection: union 成员 + interface 字段
probe('conv_union', '''query { __type(name: "ConversationUnion") { possibleTypes { name } } }''', 1500)
probe('conv_iface', '''query { __type(name: "ConversationInterface") { kind fields { name type { kind name ofType { kind name ofType { kind name } } } } } }''', 2500)
probe('entry_iface', '''query { __type(name: "ConversationEntryInterface") { kind fields { name type { kind name ofType { kind name } } } } }''', 2000)
probe('ra_entry', '''query { __type(name: "ReportAssistantConversationEntry") { kind fields { name type { kind name ofType { kind name } } } } }''', 2500)
probe('ra_conv', '''query { __type(name: "ReportAssistantConversation") { kind fields { name type { kind name ofType { kind name } } } } }''', 2500)
