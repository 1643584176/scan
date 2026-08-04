# -*- coding: utf-8 -*-
"""store Points Shop 未登录面 + login_store.js 校验逻辑确认"""
import re
import sys
import ssl
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
BASE = "https://store.steampowered.com"


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


def main():
    print("=" * 70)
    print("[1] Points Shop 未登录面")
    print("=" * 70)
    for path in ['/points/shop/', '/points/shop/c/avatar/', '/points/shop/c/profile/',
                 '/points/shop/c/background/', '/points/shop/c/animated-avatar/',
                 '/points/shop/c/emoticon/', '/points/shop/c/miniprofile/',
                 '/points/shop/c/itembundles', '/points/shop/c/profilebundles']:
        s, body, h, final = get(BASE + path)
        txt = body.decode('utf-8', 'replace')
        title = re.search(r'<title>([^<]*)</title>', txt)
        print(f"{path:45s} -> {s} len={len(body)} final={final[:60]} title={title.group(1) if title else None!r}")
        time.sleep(1)

    # points shop 页面参数
    print()
    print("--- points shop 参数反射 ---")
    for q in ['?sort=XVXZTOKEN', '?category=XVXZTOKEN', '?query=XVXZTOKEN']:
        s, body, h, final = get(BASE + '/points/shop/' + q)
        txt = body.decode('utf-8', 'replace')
        print(f"{q} -> {s} 反射={txt.count('XVXZTOKEN')}")
        time.sleep(1)

    # points API
    print()
    print("--- points API 端点 ---")
    for path in ['/points/shop/c/featured/', '/points/shop/c/search/',
                 '/points/ajaxgetitemprice/', '/points/ajaxgetbalance/',
                 '/points/shop/ajaxquery/']:
        s, body, h, final = get(BASE + path)
        txt = body.decode('utf-8', 'replace')
        print(f"{path:45s} -> {s} ct={h.get('Content-Type','')[:40]} {txt[:100]!r}")
        time.sleep(1)

    print()
    print("=" * 70)
    print("[2] login_store.js strRedirectURL 完整校验逻辑")
    print("=" * 70)
    js = open(r'D:\scan\_valve_store\js\login_store.js', encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'strRedirectURL', js):
        i = m.start()
        ctx = js[max(0, i - 150):i + 250].replace('\n', ' ')
        print(f"@{i}: ...{ctx[:400]}...")
        print()


if __name__ == '__main__':
    main()
