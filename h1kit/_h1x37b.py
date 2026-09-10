# -*- coding: utf-8 -*-
"""h1x37b: User 字段后半部分 + 找 reports/报告相关"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
q = '{ __type(name: "User") { fields(includeDeprecated: true) { name isDeprecated } } }'
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=30)
j = r.json()
names = [x['name'] for x in j['data']['__type']['fields']]
# 后半部分
for n in names[90:]:
    print(n)
