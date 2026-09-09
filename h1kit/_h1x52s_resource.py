# -*- coding: utf-8 -*-
"""h1x52s: resource(url) 解析器测试 + report_intent(id) 形态试探(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=1500):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:cut].replace('\n', ' '))
    print()

# 1. resource(url) 公开报告
probe('res_pub_report', '''query { resource(url: "https://hackerone.com/reports/2487889") { __typename url } }''')
# 2. resource(url) 私有目标 3732660
probe('res_priv_report', '''query { resource(url: "https://hackerone.com/reports/3732660") { __typename url } }''')
# 3. resource(url) 其他形态(team/user/hacktivity)
probe('res_team', '''query { resource(url: "https://hackerone.com/neon_bbp") { __typename url } }''')
probe('res_hacktivity', '''query { resource(url: "https://hackerone.com/hacktivity/2487889") { __typename url } }''')
# 4. report_intent(id) 形态试探(数字 id)
for iid in ['1', '2487889', '3732660', '3992341']:
    probe('intent_' + iid, '''query { report_intent(id: "%s") { __typename id } }''' % iid)
# 5. 公开报告的 report_intent 关联(通过 report 节点?Report 有没有 intent 字段——之前字段表里没有。试 report(2487889) 的 report_intent 不存在)
probe('intent_field_report', '''query { __type(name: "Report") { fields { name } } }''', 200)
