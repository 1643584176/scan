# -*- coding: utf-8 -*-
"""AIC 第五十二轮:resource 认证完整响应 + enduser 首页 HTML JS 考古
上轮信号:authIndexType=resource&authIndexValue=enduser -> 200。
本轮:
A. resource=enduser 完整响应 dump(多次不同 body)
B. GET /enduser/ 首页 HTML -> 提取 JS/CSS 引用 -> 下载 JS 找 API 端点
C. 从 JS 里提取 /am//openidm//iga/ 调用 -> 测试未测端点
预期结果表:
  成立 -> resource 认证返回新结构;JS 引用隐藏 API
"""
import requests, urllib3, json, time, re
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
FORM = {'Content-Type': 'application/x-www-form-urlencoded'}

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

AUTH = BASE + '/am/json/realms/alpha/authenticate'
r = S.post(AUTH, json={}, timeout=15, verify=False)
d = r.json()
authId = d['authId']
cbs = []
for cb in d.get('callbacks', []):
    t = cb['type']
    inp = [{'name': 'IDToken1', 'value': USER}] if t == 'NameCallback' else \
          [{'name': 'IDToken2', 'value': PASS}] if t == 'PasswordCallback' else \
          [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
    cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
r2 = S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
tok = r2.json().get('tokenId')
S.headers.update({'Cookie': 'aa942d46ece12ce=' + tok,
                  'Accept-API-Version': 'resource=2.1, protocol=1.0'})
print('LOGIN OK')

print('\n=== A. resource 认证完整响应 ===')
for body in [{}, {'resource': 'enduser'}, {'authId': 'x'}, {'device': 'test', 'scope': ['openid']}]:
    r = S.post(BASE + '/am/json/realms/alpha/authenticate?authIndexType=resource&authIndexValue=enduser',
               json=body, timeout=12, verify=False)
    print('body=%-40s -> %d %s' % (str(body)[:40], r.status_code, r.text[:300].replace('\n', ' ')))
    time.sleep(0.4)

print('\n=== B. enduser 首页 HTML 考古 ===')
r = S.get(BASE + '/enduser/', timeout=15, verify=False)
print('HTML status=%d len=%d' % (r.status_code, len(r.text)))
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', r.text)
links = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', r.text)
print('scripts:', scripts)
print('links:', links[:20])
all_assets = scripts + links
js_urls = []
for a in all_assets:
    if a.startswith('http'):
        u = a
    else:
        u = BASE + a if a.startswith('/') else BASE + '/enduser/' + a
    js_urls.append(u)
for u in js_urls:
    print('  ', u)
    time.sleep(0.2)

print('\n=== C. JS 内容考古 ===')
found_endpoints = set()
for u in js_urls[:15]:
    try:
        r = S.get(u, timeout=15, verify=False)
        print('%-90s -> %d len=%d' % (u[-90:], r.status_code, len(r.text)))
        if r.status_code == 200 and len(r.text) > 200:
            for pat in [r'["\'](/am/[\w/\-{}.:?=&$%]*)["\']',
                        r'["\'](/openidm/[\w/\-{}.:?=&$%]*)["\']',
                        r'["\'](/iga/[\w/\-{}.:?=&$%]*)["\']',
                        r'["\'](/enduser/[\w/\-{}.:?=&$%]*)["\']']:
                found_endpoints |= set(re.findall(pat, r.text))
            with open('D:/scan/_aic_js_dump.txt', 'a', encoding='utf-8') as f:
                f.write('\n===== %s =====\n' % u)
                f.write(r.text[:8000])
                f.write('\n')
    except Exception as e:
        print('%-90s -> ERR %s' % (u[-90:], str(e)[:50]))
    time.sleep(0.3)
print('\nJS 中引用的 API 端点:')
for e in sorted(found_endpoints):
    print('  ', e)
