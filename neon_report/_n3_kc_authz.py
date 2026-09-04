# -*- coding: utf-8 -*-
"""1) console 未认证 302 -> 官方 Keycloak 授权参数(redirect_uri/state)
2) auth 端点 400 页 kcContext 错误详情解析
3) 用官方参数复放 + 变异 redirect_uri 测试"""
import http.client, ssl, json, time, urllib.parse, re

ctx = ssl.create_default_context()
HOST = 'console-stage.neon.build'
REALM = 'staging-realm'

def req(path, method='GET', body=None, headers=None, host=HOST, no_redir=True):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8'}
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

print('=== [1] console 首页未认证 302 链 ===', flush=True)
# 逐跳跟踪(最多 6 跳)
path = '/'
hdr = {'Host': HOST}
seen = set()
for hop in range(6):
    st, raw, hdrs = req(path, headers=hdr)
    loc = hdrs.get('location', '')
    print('hop%d [%s] -> %d loc=%s' % (hop, path[:80], st, loc[:180]), flush=True)
    if st in (301, 302, 303, 307, 308) and loc:
        if loc.startswith('http'):
            u = urllib.parse.urlparse(loc)
            path = u.path + ('?' + u.query if u.query else '')
            # 换 host(如果 Location 是绝对 URL 且 host 不同)
            if u.hostname and u.hostname != HOST:
                print('  ** host switch -> %s' % u.hostname, flush=True)
                # 记录但不跟进跨 host(Keycloak 授权端点参数看 Location 字符串即可)
                print('  FULL LOC: %s' % loc, flush=True)
                break
        else:
            path = loc
    else:
        if 'kcContext' in raw:
            m = re.search(r'const kcContext = (\{.*?\});\s*\n', raw, re.S)
            if m:
                try:
                    d = json.loads(m.group(1))
                    print('  kcContext keys:', list(d.keys()), flush=True)
                    print('  pageId:', d.get('pageId'), '| msg:', str(d.get('message'))[:200], flush=True)
                    print('  realm:', d.get('realm'), '| auth:', str(d.get('auth'))[:200], flush=True)
                    # 错误信息
                    for k in ('message', 'error', 'errors'):
                        if k in d:
                            print('  %s: %s' % (k, str(d[k])[:300]), flush=True)
                except Exception as e:
                    print('  kcContext parse err', e, flush=True)
                    print('  raw head:', raw[:200].replace('\n', ' '), flush=True)
        break
    time.sleep(0.3)

print('\n=== [2] Keycloak 登录页(auth 端点无参) kcContext 全字段 ===', flush=True)
st, raw, hdrs = req('/realms/%s/protocol/openid-connect/auth' % REALM)
m = re.search(r'const kcContext = (\{.*?\});\s*\n', raw, re.S)
if m:
    try:
        d = json.loads(m.group(1))
        print('pageId:', d.get('pageId'))
        print('realm:', json.dumps(d.get('realm'), ensure_ascii=False)[:500])
        print('social:', json.dumps(d.get('social'), ensure_ascii=False)[:800])
        # 打印所有非嵌套 key
        for k, v in d.items():
            if not isinstance(v, (dict, list)):
                print('  %s = %s' % (k, str(v)[:150]))
    except Exception as e:
        print('parse err', e)
        idx = raw.find('kcContext')
        print(raw[idx:idx+1500])

print('\n=== [3] 授权端点带 PKCE + 候选 redirect(错误分类) ===', flush=True)
# 先用错误页判别:同一个 client,不带 redirect_uri(参数缺失错误) vs 带非法 redirect(白名单错误)
probes = [
    ('no_redirect', '/realms/%s/protocol/openid-connect/auth?response_type=code&client_id=neon-console&scope=openid&state=s1'),
    ('no_client', '/realms/%s/protocol/openid-connect/auth?response_type=code&redirect_uri=https://console-stage.neon.build/&scope=openid&state=s2'),
    ('no_state', '/realms/%s/protocol/openid-connect/auth?response_type=code&client_id=neon-console&redirect_uri=https://console-stage.neon.build/&scope=openid'),
    ('no_response', '/realms/%s/protocol/openid-connect/auth?client_id=neon-console&redirect_uri=https://console-stage.neon.build/&scope=openid&state=s3'),
    ('full+pkce', '/realms/%s/protocol/openid-connect/auth?response_type=code&client_id=neon-console&redirect_uri=%s&scope=openid&state=s4&code_challenge=0123456789012345678901234567890123456789012345678901234567890123&code_challenge_method=S256'),
]
for name, p in probes:
    st, raw, hdrs = req(p)
    loc = hdrs.get('location', '')
    m2 = re.search(r'const kcContext = (\{.*?\});\s*\n', raw, re.S)
    info = ''
    if m2:
        try:
            d = json.loads(m2.group(1))
            info = 'page=%s msg=%s' % (d.get('pageId'), str(d.get('message'))[:120])
            if d.get('auth'):
                info += ' | auth.err=%s' % str(d['auth'].get('error'))[:80]
        except Exception:
            info = raw[:120].replace('\n', ' ')
    elif raw.strip() and 'text/html' in hdrs.get('content-type', ''):
        info = raw[:100].replace('\n', ' ')
    print('[%s] -> %d %s loc=%s' % (name, st, info, loc[:100]), flush=True)
    time.sleep(0.3)
