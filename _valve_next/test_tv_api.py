# -*- coding: utf-8 -*-
"""pt2: steam.tv 未登录面指纹+端点 / pt3: api.steampowered.com 公开端点探测"""
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
TV = "https://steam.tv"
API = "https://api.steampowered.com"


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


def main():
    print("=" * 70)
    print("[A] steam.tv 首页指纹 + 安全头")
    print("=" * 70)
    for path in ['/', '/dota2/', '/csgo/', '/cs2/', '/valve/', '/broadcast/',
                 '/login', '/api/']:
        s, body, h, final = get(TV + path)
        txt = body.decode('utf-8', 'replace')
        title = re.search(r'<title>([^<]*)</title>', txt)
        csp = h.get('Content-Security-Policy', h.get('Content-Security-Policy-Report-Only', ''))
        print(f"{path:15s} -> {s} len={len(body):6d} final={final[:60]}")
        print(f"   title={title.group(1) if title else None!r}")
        if path in ('/', ''):
            for k in ('Server', 'X-Frame-Options', 'Strict-Transport-Security',
                      'Content-Security-Policy', 'X-Content-Type-Options', 'Set-Cookie'):
                v = h.get(k)
                if v:
                    print(f"   {k}: {v[:160]}")
        time.sleep(1)

    print()
    print("=" * 70)
    print("[B] steam.tv JS 资产与端点提取")
    print("=" * 70)
    s, body, h, final = get(TV + '/')
    txt = body.decode('utf-8', 'replace')
    js_files = []
    for m in re.finditer(r'<script[^>]+src="([^"]+)"', txt):
        js_files.append(m.group(1))
    print(f"首页 JS 引用 {len(js_files)} 个")
    for j in js_files[:20]:
        print(f"   {j}")
    # 内联 JS 中的端点
    eps = set()
    for m in re.finditer(r'["\'](/[a-zA-Z][a-zA-Z0-9_/\-\.]*(?:api|ajax|broadcast|broadcaster|stream|video)[a-zA-Z0-9_/\-\.]*)["\']', txt):
        eps.add(m.group(1))
    for m in re.finditer(r'https?://[a-zA-Z0-9\.\-]*steam[a-zA-Z0-9\.\-/]*', txt):
        eps.add(m.group(0))
    for e in sorted(eps):
        if len(e) < 120:
            print(f"   EP: {e}")

    print()
    print("=" * 70)
    print("[C] steam.tv 参数反射")
    print("=" * 70)
    for q in ['?channel=XVXZTOKEN', '?game=XVXZTOKEN', '?broadcaster=XVXZTOKEN',
              '?id=XVXZTOKEN', '?ref=XVXZTOKEN', '?lang=XVXZTOKEN']:
        s, body, h, final = get(TV + '/' + q)
        txt = body.decode('utf-8', 'replace')
        print(f"{q:25s} -> {s} 反射={txt.count('XVXZTOKEN')}")
        time.sleep(0.8)

    print()
    print("=" * 70)
    print("[D] api.steampowered.com 公开端点探测")
    print("=" * 70)
    apis = [
        # IStoreService (需 key,看错误信息差异)
        ('/ISteamWebAPIUtil/GetServerInfo/v1/', 'GET'),
        ('/ISteamWebAPIUtil/GetSupportedAPIList/v1/', 'GET'),
        ('/ISteamUser/GetPlayerSummaries/v0002/?steamids=76561197960434622', 'GET'),
        ('/ISteamUser/GetFriendList/v0001/?steamid=76561197960434622', 'GET'),
        ('/ISteamUser/GetPlayerBans/v1/?steamids=76561197960434622', 'GET'),
        ('/ISteamUser/GetUserGroupList/v1/?steamid=76561197960434622', 'GET'),
        ('/ISteamUser/ResolveVanityURL/v0001/?vanityurl=gabe', 'GET'),
        ('/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=570', 'GET'),
        ('/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/?gameid=570', 'GET'),
        ('/ISteamUserStats/GetSchemaForGame/v2/?appid=570', 'GET'),
        ('/ISteamApps/GetAppList/v2/', 'GET'),
        ('/ISteamApps/GetAppList/v0001/', 'GET'),
        ('/ISteamApps/GetServersAtAddress/v1/?addr=127.0.0.1', 'GET'),
        ('/ISteamApps/UpToDateCheck/v1/?appid=570&version=1', 'GET'),
        ('/ISteamNews/GetNewsForApp/v0002/?appid=570&count=1', 'GET'),
        ('/ISteamNews/GetNewsForAppAuthed/v0002/?appid=570&count=1', 'GET'),
        ('/ISteamNews/GetNewsForApp/v2/?appid=570&count=1&maxlength=10', 'GET'),
        ('/ISteamRemoteStorage/GetPublishedFileDetails/v1/', 'POST'),
        ('/ISteamRemoteStorage/GetUGCFileDetails/v1/?appid=570&ugcid=1', 'GET'),
        ('/ISteamRemoteStorage/EnumerateUserPublishedFiles/v1/?steamid=76561197960434622', 'GET'),
        ('/IPlayerService/GetOwnedGames/v0001/?steamid=76561197960434622', 'GET'),
        ('/IPlayerService/GetRecentlyPlayedGames/v0001/?steamid=76561197960434622', 'GET'),
        ('/IPlayerService/GetSteamLevel/v0001/?steamid=76561197960434622', 'GET'),
        ('/IPlayerService/GetBadges/v0001/?steamid=76561197960434622', 'GET'),
        ('/IPlayerService/GetCommunityBadgeProgress/v0001/?steamid=76561197960434622', 'GET'),
        ('/ISteamLeaderboards/GetLeaderboardsForGame/v0002/?appid=570', 'GET'),
        ('/ISteamWebUserPresenceOAuth/GetFriendsList/v0001/?steamid=76561197960434622', 'GET'),
        ('/ISteamUserAuth/AuthenticateUser/v0001/?steamid=76561197960434622', 'GET'),
        ('/ISteamWebAPIUtil/GetServerInfo/v0001/', 'GET'),
        ('/ISteamDirectory/GetCMList/v1/?cellid=0', 'GET'),
        ('/ISteamApps/GetAppList/v0002/?key=&format=json', 'GET'),
    ]
    for path, method in apis:
        if method == 'GET':
            s, body, h, final = get(API + path)
        else:
            # POST 简单处理
            req = urllib.request.Request(API + path, data=b'itemcount=1&publishedfileids[0]=1',
                                         headers={'User-Agent': UA})
            try:
                resp = urllib.request.urlopen(req, context=CTX, timeout=20)
                s, body, final = resp.status, resp.read(), resp.geturl()
            except urllib.error.HTTPError as e:
                s, body, final = e.code, e.read(), e.geturl()
            except Exception as e:
                s, body, final = 0, str(e).encode(), ''
        txt = body.decode('utf-8', 'replace')[:200].replace('\n', ' ')
        print(f"{path[:72]:72s} -> {s} {txt[:110]!r}")
        time.sleep(0.5)


if __name__ == '__main__':
    main()
