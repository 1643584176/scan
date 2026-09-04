# -*- coding: utf-8 -*-
"""AIC 第九轮:/openidm/policy 完整内容 + privilege 详情"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJkYjNkNjM1Ni02MWEwLTQ2ODQtOWVhYS1jMTM1M2RmYTQ0ZDkiLCJjdHMiOiJPQVVUSDJfU1RBVEVMRVNTX0dSQU5UIiwiYXV0aF9sZXZlbCI6MCwiYXVkaXRUcmFja2luZ0lkIjoiZWFiYWVmY2UtODJkZi00NDYyLTkwZTctMTk1YmZkNTAwMDQ1LTM4ODYzNiIsInN1Ym5hbWUiOiJkYjNkNjM1Ni02MWEwLTQ2ODQtOWVhYS1jMTM1M2RmYTQ0ZDkiLCJpc3MiOiJodHRwczovL29wZW5hbS1idWctYm91bnR5LXN0YWcuZm9yZ2VibG9ja3MuY29tOjQ0My9hbS9vYXV0aDIvYWxwaGEiLCJ0b2tlbk5hbWUiOiJhY2Nlc3NfdG9rZW4iLCJ0b2tlbl90eXBlIjoiQmVhcmVyIiwiYXV0aEdyYW50SWQiOiI0a3JYWWRsWVdmX2tKZ2ZWRjVGUWlsb09XdFkiLCJjbGllbnRfaWQiOiJlbmRVc2VyVUlDbGllbnQiLCJhdWQiOiJlbmRVc2VyVUlDbGllbnQiLCJuYmYiOjE3ODgyNDc4NzAsImdyYW50X3R5cGUiOiJhdXRob3JpemF0aW9uX2NvZGUiLCJzY29wZSI6WyJmcjppZG06KiJdLCJhdXRoX3RpbWUiOjE3ODgyNDc4NjUsInJlYWxtIjoiL2FscGhhIiwiZXhwIjoxNzg4MjUxNDcwLCJpYXQiOjE3ODgyNDc4NzAsImV4cGlyZXNfaW4iOjM2MDAsImp0aSI6IlFoM2FQQ2Z0SFR4bEx6cElHUlNkekwwSFIyVSJ9.ustwJpOA-B0vA9J0aQm1UueFlyaEp5fKUzwe4EaryX8'
COOKIE = 'amlbcookie=01; aa942d46ece12ce=tvVfNxaXuVbrr2BzbooZZTz8iTk.*AAJTSQACMDIAAlNLABxZNXdTYkVsVmxPdWdiRlZkeDc3V3doNTJ1VTg9AAR0eXBlAANDVFMAAlMxAAIwMQ..*'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'research-1643',
                  'Authorization': 'Bearer ' + TOKEN,
                  'Cookie': COOKIE,
                  'Accept-API-Version': 'resource=1.0, protocol=1.0'})

r = S.get(BASE + '/openidm/policy', timeout=15, verify=False)
print('policy status:', r.status_code)
body = r.text
with open(r'D:\scan\_aic_policy.json', 'w', encoding='utf-8') as f:
    f.write(body)
print('saved, len:', len(body))
# 提取 resource 名 + 策略概要
try:
    j = r.json()
    for res in j.get('resources', []):
        props = [p['name'] for p in res.get('properties', [])]
        print('resource:', res.get('resource') or res.get('name'), 'props:', props[:20])
except Exception as e:
    print('parse err:', e)
    print(body[:800])
