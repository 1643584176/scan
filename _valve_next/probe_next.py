# -*- coding: utf-8 -*-
"""下一批目标快速指纹:partner.steamgames.com / steam.tv / api.steampowered.com"""
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


def get(url, timeout=20, referer=None):
    h = {'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'}
    if referer:
        h['Referer'] = referer
    r = urllib.request.Request(url, headers=h)
    try:
        resp = urllib.request.urlopen(r, context=CTX, timeout=timeout)
        return resp.status, resp.read(), dict(resp.headers), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers), e.geturl()
    except Exception as e:
        return 0, str(e).encode(), {}, ''


def show(tag, s, body, h, final_url, max_head=200):
    print(f"[{tag}] status={s} len={len(body)} final={final_url[:90]}")
    for k in ['Server', 'Content-Type', 'X-Frame-Options', 'Content-Security-Policy',
              'Strict-Transport-Security', 'Location', 'Set-Cookie']:
        v = h.get(k)
        if v:
            print(f"    {k}: {str(v)[:160]}")
    return body


def main():
    # ===== partner.steamgames.com =====
    print("=" * 70)
    print("[1] partner.steamgames.com")
    print("=" * 70)
    for path in ['/', '/login/', '/home/', '/dashboard/']:
        s, body, h, final = get('https://partner.steamgames.com' + path)
        b = show(path, s, body, h, final)
        if s == 200:
            txt = b.decode('utf-8', 'replace')
            m = re.search(r'<title>([^<]*)</title>', txt)
            print(f"    title: {m.group(1) if m else None}")
            for mm in list(re.finditer(r'<script[^>]*src="([^"]+)"', txt))[:8]:
                print("    js:", mm.group(1)[:100])
            for mm in list(re.finditer(r'<form[^>]*action="([^"]*)"', txt))[:3]:
                print("    form:", mm.group(1)[:100])
        time.sleep(1)

    # ===== steam.tv =====
    print()
    print("=" * 70)
    print("[2] steam.tv")
    print("=" * 70)
    for path in ['/', '/watch/', '/api/']:
        s, body, h, final = get('https://steam.tv' + path)
        b = show(path, s, body, h, final)
        if s == 200 and b:
            txt = b.decode('utf-8', 'replace')
            m = re.search(r'<title>([^<]*)</title>', txt)
            print(f"    title: {m.group(1) if m else None}")
            for mm in list(re.finditer(r'<script[^>]*src="([^"]+)"', txt))[:8]:
                print("    js:", mm.group(1)[:110])
            # api 端点线索
            for mm in list(re.finditer(r'["\'](/[a-zA-Z][a-zA-Z0-9_\-/\.]*api[a-zA-Z0-9_\-/\.]*)["\']', txt))[:10]:
                print("    api:", mm.group(1)[:100])
        time.sleep(1)

    # ===== api.steampowered.com =====
    print()
    print("=" * 70)
    print("[3] api.steampowered.com 公开端点")
    print("=" * 70)
    public_eps = [
        '/ISteamApps/GetAppList/v2/',
        '/ISteamApps/GetServersAtAddress/v1/?addr=127.0.0.1',
        '/ISteamNews/GetNewsForApp/v2/?appid=570&count=1',
        '/ISteamUser/GetPlayerSummaries/v2/?steamids=76561197960434622',
        '/ISteamUser/GetPlayerBans/v1/?steamids=76561197960434622',
        '/IPlayerService/GetOwnedGames/v1/?steamid=76561197960434622',
        '/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=570',
        '/ISteamWebAPIUtil/GetServerInfo/v1/',
        '/ISteamWebAPIUtil/GetSupportedAPIList/v1/',
        '/ITFItems_570/GetPlayerItems/v1/?steamid=76561197960434622',
        '/ISteamRemoteStorage/GetPublishedFileDetails/v1/',
    ]
    for ep in public_eps:
        s, body, h, final = get('https://api.steampowered.com' + ep)
        b = body.decode('utf-8', 'replace')
        print(f"{ep:60s} -> {s} len={len(b)} {b[:90]!r}")
        time.sleep(1)

    # ===== community.akamai.steamstatic.com =====
    print()
    print("=" * 70)
    print("[4] community.akamai.steamstatic.com (静态 CDN)")
    print("=" * 70)
    for path in ['/', '/public/javascript/game.js', '/public/css/global.css']:
        s, body, h, final = get('https://community.akamai.steamstatic.com' + path)
        show(path, s, body, h, final, max_head=120)
        time.sleep(1)


if __name__ == '__main__':
    main()
