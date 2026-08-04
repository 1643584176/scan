# -*- coding: utf-8 -*-
"""cs1/tf1/vs1: counter-strike.net + teamfortress.com + valvesoftware.com 指纹+JS+参数反射"""
import re
import sys
import ssl
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

SITES = {
    'CS': ('https://www.counter-strike.net', ['/', '/news/', '/cs2/', '/game/',
                                              '/merch/', '/events/', '/news/updates/',
                                              '/search/']),
    'TF': ('https://www.teamfortress.com', ['/', '/news/', '/game/',
                                            '/tickets/', '/stats.php', '/stats/',
                                            '/posters.php']),
    'VS': ('https://www.valvesoftware.com', ['/', '/en/', '/games/',
                                             '/about/', '/jobs/']),
}


def get(url, timeout=20):
    h = {'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'}
    r = urllib.request.Request(url, headers=h)
    try:
        resp = urllib.request.urlopen(r, context=CTX, timeout=timeout)
        return resp.status, resp.read(), dict(resp.headers), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers), e.geturl()
    except Exception as e:
        return 0, str(e).encode(), {}, ''


def scan_site(name, base, paths):
    print("=" * 70)
    print(f"[{name}] {base} 页面指纹 + 安全头")
    print("=" * 70)
    js_files = set()
    for path in paths:
        s, body, h, final = get(base + path)
        txt = body.decode('utf-8', 'replace')
        title = re.search(r'<title>([^<]*)</title>', txt)
        print(f"{path:20s} -> {s} len={len(body):6d} final={final[:55]}")
        print(f"   title={title.group(1) if title else None!r}")
        if path == '/' or s == 200 and path in ('/', ''):
            for k in ('Server', 'X-Frame-Options', 'Strict-Transport-Security',
                      'Content-Security-Policy', 'X-Content-Type-Options',
                      'X-XSS-Protection'):
                v = h.get(k)
                if v:
                    print(f"   {k}: {v[:150]}")
        # 收集 JS
        for m in re.finditer(r'<script[^>]+src="([^"]+)"', txt):
            j = m.group(1)
            if j.startswith('/'):
                js_files.add(base + j)
            elif j.startswith('http'):
                js_files.add(j)
        time.sleep(0.8)

    print()
    print(f"--- [{name}] 页面内联端点/API 提取 ---")
    s, body, h, final = get(base + '/')
    txt = body.decode('utf-8', 'replace')
    eps = set()
    for m in re.finditer(r'["\'](/[a-zA-Z][a-zA-Z0-9_/\-\.]*(?:api|ajax|json|action|submit|search|update|get)[a-zA-Z0-9_/\-\.]*)["\']', txt):
        ep = m.group(1)
        if len(ep) < 80 and not ep.endswith(('.js', '.css', '.png', '.jpg', '.gif', '.svg')):
            eps.add(ep)
    for m in re.finditer(r'https?://[a-zA-Z0-9\.\-]*(?:steam|valve|counter-strike|teamfortress)[a-zA-Z0-9\.\-/]*', txt):
        u = m.group(0)
        if len(u) < 100:
            eps.add(u)
    for e in sorted(eps):
        print(f"   EP: {e}")

    print()
    print(f"--- [{name}] 参数反射 ---")
    for q in ['?q=XVXZTOKEN', '?id=XVXZTOKEN', '?page=XVXZTOKEN', '?lang=XVXZTOKEN',
              '?search=XVXZTOKEN', '?query=XVXZTOKEN', '?appid=XVXZTOKEN']:
        s, body, h, final = get(base + '/' + q)
        txt = body.decode('utf-8', 'replace')
        if txt.count('XVXZTOKEN') > 0:
            print(f"   {q:25s} -> {s} 反射={txt.count('XVXZTOKEN')}")
        time.sleep(0.5)

    # 下载首页引用的 JS 并提取端点
    print()
    print(f"--- [{name}] JS 资产下载+端点提取 ---")
    import os
    outdir = r'D:\scan\_valve_next'
    count = 0
    all_eps = set()
    for j in sorted(js_files):
        if count >= 12:
            break
        try:
            req = urllib.request.Request(j, headers={'User-Agent': UA})
            resp = urllib.request.urlopen(req, context=CTX, timeout=25)
            data = resp.read()
            if len(data) < 5000:
                continue
            fname = re.sub(r'[^a-zA-Z0-9]', '_', j.split('/')[-1][:60]) + '.js'
            fpath = os.path.join(outdir, name.lower() + '_' + fname)
            open(fpath, 'wb').write(data)
            count += 1
            print(f"   {j[:80]} -> {len(data)//1024} KB")
            txt = data.decode('utf-8', 'replace')
            for m in re.finditer(r'["\'](/[a-zA-Z][a-zA-Z0-9_/\-\.]*(?:api|ajax|json|action|submit|search|update|get|post)[a-zA-Z0-9_/\-\.]*)["\']', txt):
                ep = m.group(1)
                if len(ep) < 90 and not ep.endswith(('.js', '.css', '.png', '.jpg', '.gif', '.svg', '.woff')):
                    all_eps.add(ep)
        except Exception as e:
            print(f"   {j[:80]} -> ERR {e}")
        time.sleep(0.5)
    for e in sorted(all_eps):
        print(f"   JS-EP: {e}")


def main():
    for name, (base, paths) in SITES.items():
        try:
            scan_site(name, base, paths)
        except Exception as e:
            print(f"[{name}] scan failed: {e}")
        print()


if __name__ == '__main__':
    main()
