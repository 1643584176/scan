# -*- coding: utf-8 -*-
"""h1x53j: conversation(id) 完整语法重测(双层 inline fragment)"""
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=1000):
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=15)
        print('%-42s [%s] %s' % (name, r.status_code, r.text[:cut].replace('\n', ' ')))
    except Exception as e:
        print('%-42s ERR %s' % (name, e))
    time.sleep(0.3)

# entries 是 LIST,每个元素是 ConversationEntryUnion(ConversationEntry | ReportAssistantConversationEntry)
F = ('''... on ConversationInterface { id type entries { ... on ConversationEntryInterface { id type created_at data actor { username } } } }''')
probe('conv_1', '''query { conversation(id: "1") { %s } }''' % F)
probe('conv_3732660', '''query { conversation(id: "3732660") { %s } }''' % F)
probe('conv_gid_conv', '''query { conversation(id: "gid://hackerone/ReportAssistantConversation/1") { %s } }''' % F)
probe('conv_gid_conv_big', '''query { conversation(id: "gid://hackerone/ReportAssistantConversation/3732660") { %s } }''' % F)
probe('conv_gid_validation', '''query { conversation(id: "gid://hackerone/ValidationAgentConversation/1") { %s } }''' % F)
