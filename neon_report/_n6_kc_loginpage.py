# -*- coding: utf-8 -*-
"""1) kcContext 完整 dump(去尾逗号)
2) kc_idp_hint 矩阵(auth 端点直接跳 IDP)
3) console /auth/keycloak/callback 行为(官方 redirect_uri 处理端)
4) password 登录表单是否开启(登录页字段)"""
import http.client, ssl, json, time, urllib.parse, re

ctx = ssl.create_default_context()
HOST = 'console-stage.neon.build'
REALM = 'staging-realm'
CLIENT = 'neon-console'
RU = 'https://console-stage.neon.build/auth/keycloak/callback'

def req(path, method='GET', body=None, headers=None, host=HOST):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0', 'Accept': '*/*'}
        if body is not None:
            h['Content-Type'] = 'application/x-www-form-urlencoded'
        if headers:
            h.update(headers)
        conn.request(method, path, body=body, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        conn.close()
        return st, raw.decode('utf-8', 'replace'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}

def parse_kc(raw):
    i = raw.find('const kcContext = ')
    if i < 0:
        return None
    i = raw.find('{', i)
    depth = 0
    in_str = False
    esc = False
    j = i
    while j < len(raw):
        c = raw[j]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    break
        j += 1
    s = raw[i:j + 1]
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    # 去尾逗号(Keycloak 模板 JS 对象字面量)
    s = re.sub(r',\s*([}\]])', r'\1', s)
    try:
        return json.loads(s)
    except Exception as e:
        print('  JSON err:', e)
        return None

print('=== [1] 登录页完整画像 ===', flush=True)
p = '/realms/%s/protocol/openid-connect/auth?client_id=%s&redirect_uri=%s&response_type=code&scope=openid+profile+email&state=zzz' % (
    REALM, CLIENT, urllib.parse.quote(RU, safe=''))
st, raw, hdrs = req(p)
d = parse_kc(raw)
if d:
    print('pageId:', d.get('pageId'))
    print('-- social --')
    for prov in (d.get('social') or {}).get('providers', []):
        print('  %s | alias=%s' % (prov.get('displayName'), prov.get('alias')))
    print('-- login 表单字段 --')
    for k, v in d.items():
        if k in ('usernameHidden', 'registrationDisabled', 'realm', 'passwordRequired', 'social', 'loginUpdateUsernameHidden'):
            print('  %s = %s' % (k, json.dumps(v, ensure_ascii=False)[:400]))
    print('-- 非嵌套字段 --')
    for k, v in d.items():
        if not isinstance(v, (dict, list)) and k not in ('social',):
            print('  %s = %s' % (k, str(v)[:100]))
    # scripts(可能泄露版本)
    if 'scripts' in raw:
        m = re.findall(r'src="([^"]+)"', raw)
        for s in m[:10]:
            print('  script:', s)
else:
    print('parse fail raw:', raw[:300].replace('\n', ' '))

print('\n=== [2] kc_idp_hint 矩阵 ===', flush=True)
for hint in ['google', 'github', 'hasura', 'microsoft', 'nonexistent', 'oidc', '']:
    extra = '&kc_idp_hint=%s' % hint if hint else ''
    p2 = '/realms/%s/protocol/openid-connect/auth?client_id=%s&redirect_uri=%s&response_type=code&scope=openid&state=h1%s' % (
        REALM, CLIENT, urllib.parse.quote(RU, safe=''), extra)
    st2, raw2, hdrs2 = req(p2)
    loc = hdrs2.get('location', '')
    ct = hdrs2.get('content-type', '')
    if st2 == 302:
        print('[hint=%s] -> 302 %s' % (hint or '(none)', loc[:200]), flush=True)
    else:
        d2 = parse_kc(raw2)
        info = 'page=%s' % (d2 or {}).get('pageId') if d2 else raw2[:80].replace('\n', ' ')
        print('[hint=%s] -> %d %s' % (hint or '(none)', st2, info), flush=True)
    time.sleep(0.3)

print('\n=== [3] console callback 行为 ===', flush=True)
# 官方 redirect_uri 端点(无参/错参/带 code)
for q in ['', '?code=fakecode123&state=zzz', '?error=access_denied&error_description=denied&state=zzz',
          '?code=fake&state=zzz&session_state=abc']:
    p3 = '/auth/keycloak/callback' + q
    st3, raw3, hdrs3 = req(p3)
    loc = hdrs3.get('location', '')
    ct = hdrs3.get('content-type', '')
    print('[cb %s] -> %d CT=%s loc=%s body=%s' % (q[:60] or '(plain)', st3, ct[:25], loc[:130], raw3[:100].replace('\n', ' ')), flush=True)
    time.sleep(0.3)
