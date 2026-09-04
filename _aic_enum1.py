# -*- coding: utf-8 -*-
"""AIC (ForgeRock AM) 第一轮:匿名面端点枚举
预期结果表:
  成立(正常) -> 未认证访问受保护端点返回 401/403;公开端点返回 200/302
  不成立(发现) -> 受保护端点返回 200 或返回敏感数据(用户/会话/策略/配置)
  判定:状态码异常 + 响应体含敏感关键词 = 高价值;两轮内无法区分 -> 放弃该端点
规则:直连禁代理(trust_env=False);只做 GET/HEAD,不写任何数据
"""
import requests, urllib3
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers['User-Agent'] = 'research-1643'

PATHS = [
    '/', '/login/',
    # 版本/健康
    '/am/version', '/am/isAlive.jsp', '/am/healthcheck', '/am/info',
    '/am/json/version', '/am/json/serverinfo/alpha',
    # JSON REST API
    '/am/json/realms/alpha/authenticate', '/am/json/realms/alpha/users',
    '/am/json/realms/alpha/sessions', '/am/json/realms/alpha/policies',
    '/am/json/realms/alpha/selfservice/registration',
    '/am/json/realms/alpha/selfservice/passwordReset',
    '/am/json/realms/root/realms', '/am/json/realms/alpha/realm-config',
    '/am/json/realms/alpha/applications', '/am/json/realms/alpha/groups',
    '/am/json/realms/alpha/devices',
    # OIDC / OAuth2
    '/am/oauth2/.well-known/openid-configuration',
    '/am/oauth2/realms/alpha/.well-known/openid-configuration',
    '/am/oauth2/realms/root/.well-known/openid-configuration',
    '/am/oauth2/authorize', '/am/oauth2/access_token',
    '/am/oauth2/realms/alpha/authorize', '/am/oauth2/realms/alpha/access_token',
    # SAML
    '/am/saml/consent', '/am/saml/redirect/alias/alpha',
    # 遗留/其他
    '/am/restful-security/authenticate', '/am/restful-security/sessions',
    '/am/enduser/', '/am/XUI/', '/am/console/',
    '/am/idm/endpoint/selfservice/registration',
    '/openam/json/realms/alpha/authenticate',
    '/am/umbraco/config',
]

SENS = ['"realm"', '"userName"', '"tokenId"', '"access_token"', '"session"',
        '"policies"', '"error"', 'Uncaught', 'stacktrace', 'version']

print('=== AIC 匿名面枚举 ===')
print('%-60s %-5s %-30s %s' % ('PATH', 'CODE', 'CTYPE', 'SENS/HINT'))
for p in PATHS:
    try:
        r = S.get(BASE + p, timeout=12, verify=False, allow_redirects=False)
        body = r.text[:300]
        hit = [k for k in SENS if k in body]
        ctype = (r.headers.get('Content-Type') or '')[:28]
        hint = ','.join(hit) if hit else (r.headers.get('Server') or '')[:20]
        print('%-60s %-5s %-30s %s' % (p, r.status_code, ctype, hint))
    except Exception as e:
        print('%-60s ERR  %s' % (p, str(e)[:60]))
