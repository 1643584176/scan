# -*- coding: utf-8 -*-
"""pt6: 找私密愿望单用户,对比网页 vs API"""
import re
import sys
import ssl
import time
import random
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
API = "https://api.steampowered.com"
COMM = "https://steamcommunity.com"


def get(url, timeout=25):
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
    # 0. 网页端可达性确认
    print("[0] steamcommunity 可达性")
    s, body, h, final = get(COMM + '/', timeout=30)
    print(f"   GET / -> {s} len={len(body)}")
    time.sleep(1)

    # 1. 用已知活跃用户(Valve 官方群组/随机)快速探测网页行为
    print()
    print("[1] 探测几个知名用户的 wishlist 网页行为")
    known = ['76561197960434622',      # gabe
             '76561198006409504',      # valve 测试
             '76561198046992582',
             '76561198183721740',
             ]
    for sid in known:
        s, body, h, final = get(COMM + f'/wishlist/{sid}')
        txt = body.decode('utf-8', 'replace')
        title = re.search(r'<title>([^<]*)</title>', txt)
        t = title.group(1) if title else ''
        # 隐私状态关键词
        priv = re.search(r'(?:This (?:user\'s )?wishlist is (?:private|friends only)|wishlist.*(?:private|friends only)|Friends Only)', txt, re.I)
        items = len(re.findall(r'data-appid="(\d+)"', txt))
        print(f"   {sid}: {s} title={t[:40]!r} items={items} private={'YES' if priv else 'no'}")
        if priv:
            print(f"      私密提示: {priv.group(0)}")
        time.sleep(0.8)

    # 2. 随机扫 60 个 ID 找私密用户
    print()
    print("[2] 随机扫描找私密愿望单用户(60 个)")
    random.seed(42)
    found = []
    for i in range(60):
        acc = random.randint(500000, 600000000)
        sid2 = 76561197960265728 + acc
        s, body, h, final = get(COMM + f'/wishlist/{sid2}')
        txt = body.decode('utf-8', 'replace')
        if s != 200:
            continue
        priv = re.search(r'(?:wishlist is (?:private|friends only)|Friends Only|private)', txt, re.I)
        items = len(re.findall(r'data-appid="(\d+)"', txt))
        title = re.search(r'<title>([^<]*)</title>', txt)
        if priv or items == 0:
            print(f"   [{i}] {sid2}: {s} title={title.group(1) if title else ''!r} items={items} private={'YES' if priv else '?'}")
            found.append((sid2, bool(priv)))
            if len(found) >= 4:
                break
        time.sleep(0.5)

    # 3. 对找到的用户做 API 对比
    print()
    print("[3] API vs 网页对比")
    for sid2, is_priv in found:
        s2, b2, h2, f2 = get(API + f'/IWishlistService/GetWishlist/v1/?steamid={sid2}')
        t2 = b2.decode('utf-8', 'replace')
        api_items = len(re.findall(r'"appid"', t2))
        print(f"   steamid={sid2} 网页私密={is_priv} API={s2} API物品数={api_items} resp={t2[:120]!r}")
        time.sleep(0.6)

    # 4. 对照:不存在的 steamid
    print()
    print("[4] 对照:不存在/无效 steamid")
    for bad in ['1', '76561197960265728', '99999999999999999']:
        s, body, h, final = get(API + f'/IWishlistService/GetWishlist/v1/?steamid={bad}')
        print(f"   steamid={bad} -> {s} {body.decode('utf-8','replace')[:100]!r}")
        time.sleep(0.5)


if __name__ == '__main__':
    main()
