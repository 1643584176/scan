# -*- coding: utf-8 -*-
"""pt5: 验证 GetWishlist/GetGamesFollowed 未登录访问 vs 网页隐私设置"""
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
API = "https://api.steampowered.com"
COMM = "https://steamcommunity.com"


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
    # 1. 已知用户 gabe(公开 profile)网页愿望单行为
    sid = '76561197960434622'
    print("=" * 70)
    print("[1] 网页端愿望单(公开用户)")
    print("=" * 70)
    s, body, h, final = get(COMM + f'/wishlist/{sid}')
    txt = body.decode('utf-8', 'replace')
    title = re.search(r'<title>([^<]*)</title>', txt)
    print(f"GET /wishlist/{sid} -> {s} title={title.group(1) if title else None!r} len={len(body)}")
    if 'wishlist_privatenote' in txt or 'is_private' in txt:
        print("   包含私密标记")
    m = re.search(r'private_wishlist[^<]{0,40}', txt)
    if m:
        print(f"   私密标志: {m.group(0)}")
    time.sleep(1)

    # 2. API 未登录访问
    print()
    print("=" * 70)
    print("[2] API 未登录(无 cookie 无 key)")
    print("=" * 70)
    for path in [
        f'/IWishlistService/GetWishlist/v1/?steamid={sid}',
        f'/IWishlistService/GetWishlistItemCount/v1/?steamid={sid}',
        f'/IStoreService/GetGamesFollowed/v1/?steamid={sid}',
    ]:
        s, body, h, final = get(API + path)
        txt = body.decode('utf-8', 'replace')[:300].replace('\n', ' ')
        print(f"{path.split('?')[0][:55]:55s} -> {s}")
        print(f"   {txt[:260]!r}")
        time.sleep(0.8)

    # 3. 找私密 profile 用户:随机 steamid 扫描(限 20 个,仅测愿望单隐私设置)
    print()
    print("=" * 70)
    print("[3] 私密 profile 用户愿望单泄露测试(随机 ID,限制 20 个)")
    print("=" * 70)
    # steamid64 = 76561197960265728 + accountid
    import random
    random.seed(2026)
    checked = 0
    for _ in range(40):
        acc = random.randint(100000, 900000000)
        sid2 = 76561197960265728 + acc
        # 先看网页 profile 是否私密(通过 wishlist 页)
        s, body, h, final = get(COMM + f'/wishlist/{sid2}')
        txt = body.decode('utf-8', 'replace')
        title = re.search(r'<title>([^<]*)</title>', txt)
        t = title.group(1) if title else ''
        # 私密愿望单时页面会显示什么?
        if 'wishlist' in txt and ('private' in txt.lower() or 'Friends Only' in txt or 'only you' in txt.lower()):
            print(f"   steamid={sid2} 网页显示: {t} | 私密提示={re.search(r'[^<>]{0,60}(?:private|Friends Only|only you)[^<>]{0,60}', txt, re.I).group(0) if re.search(r'[^<>]{0,60}(?:private|Friends Only|only you)[^<>]{0,60}', txt, re.I) else '?'}")
            # API 对比
            s2, b2, h2, f2 = get(API + f'/IWishlistService/GetWishlist/v1/?steamid={sid2}')
            t2 = b2.decode('utf-8', 'replace')[:200]
            print(f"       API -> {s2} {t2[:180]!r}")
            checked += 1
            if checked >= 3:
                break
        time.sleep(0.4)
    print(f"   找到私密用户: {checked}")

    # 4. 网页端正常用户愿望单与 API 响应一致性
    print()
    print("=" * 70)
    print("[4] 对比:API 返回 vs 网页显示(非私密用户)")
    print("=" * 70)
    s, body, h, final = get(API + f'/IWishlistService/GetWishlist/v1/?steamid={sid}')
    api_items = len(re.findall(r'"appid"', body.decode('utf-8', 'replace')))
    s2, body2, h2, f2 = get(COMM + f'/wishlist/{sid}')
    html = body2.decode('utf-8', 'replace')
    html_count = len(re.findall(r'data-appid="(\d+)"', html))
    print(f"   API 物品数: {api_items}, 网页 data-appid 数: {html_count}")


if __name__ == '__main__':
    main()
