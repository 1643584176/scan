# -*- coding: utf-8 -*-
"""pt7: steamcommunity 网络诊断 + playartifact + 剩余目标快速探测"""
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


def get(url, timeout=30):
    h = {'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'}
    r = urllib.request.Request(url, headers=h)
    try:
        resp = urllib.request.urlopen(r, context=CTX, timeout=timeout)
        return resp.status, resp.read(), dict(resp.headers), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers), e.geturl()
    except Exception as e:
        return 0, str(e).encode(), {}, ''


def main():
    # 1. steamcommunity 可达性诊断:不同路径
    print("=" * 70)
    print("[1] steamcommunity 可达性诊断")
    print("=" * 70)
    for p in ['/', '/wishlist/76561197960434622', '/market/', '/search?text=test',
              '/id/valve', '/profiles/76561197960434622']:
        t0 = time.time()
        s, body, h, final = get('https://steamcommunity.com' + p, timeout=35)
        dt = time.time() - t0
        print(f"   {p:40s} -> {s} len={len(body)} {dt:.1f}s")
    time.sleep(1)

    # 2. playartifact.com(scope 内未测)
    print()
    print("=" * 70)
    print("[2] playartifact.com(scope 内)")
    print("=" * 70)
    for url in ['https://www.playartifact.com/',
                'https://playartifact.com/',
                'https://www.playartifact.com/cards/',
                'https://www.playartifact.com/d/']:
        t0 = time.time()
        s, body, h, final = get(url, timeout=25)
        txt = body.decode('utf-8', 'replace')
        title = re.search(r'<title>([^<]*)</title>', txt)
        xfo = h.get('X-Frame-Options', '')
        csp = h.get('Content-Security-Policy', '')[:60]
        print(f"   {url:45s} -> {s} len={len(body)} {time.time()-t0:.1f}s title={title.group(1)[:30] if title else ''!r}")
        if xfo or csp:
            print(f"        XFO={xfo} CSP={csp}")
    time.sleep(1)

    # 3. teamfortress.com / valvesoftware.com 补充(未在 scope 的确认)
    print()
    print("=" * 70)
    print("[3] 补充:steamgames.com / steampowered.com 边界确认")
    print("=" * 70)
    for url in ['https://www.steamgames.com/',
                'https://store.steampowered.com/',
                'https://list.valvesoftware.com/',
                'https://translation.steampowered.com/']:
        t0 = time.time()
        s, body, h, final = get(url, timeout=25)
        txt = body.decode('utf-8', 'replace')
        title = re.search(r'<title>([^<]*)</title>', txt)
        print(f"   {url:45s} -> {s} len={len(body)} {time.time()-t0:.1f}s title={title.group(1)[:30] if title else ''!r}")


if __name__ == '__main__':
    main()
