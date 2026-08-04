# -*- coding: utf-8 -*-
"""pt9: 轮询等待 api.steampowered.com 恢复,恢复后立即执行关键验证"""
import json
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


def get(url, timeout=15):
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
    print(f"[{time.strftime('%H:%M:%S')}] 开始轮询 api.steampowered.com ...", flush=True)
    ok = False
    for i in range(40):  # 最多 40 * 30s = 20 分钟
        s, body, h, final = get(API + '/ISteamWebAPIUtil/GetServerInfo/v1/', timeout=12)
        if s == 200:
            print(f"[{time.strftime('%H:%M:%S')}] 第{i}轮: 可达! {body[:80]!r}", flush=True)
            ok = True
            break
        if i % 4 == 0:
            print(f"[{time.strftime('%H:%M:%S')}] 第{i}轮: 仍不可达 ({s})", flush=True)
        time.sleep(30)
    if not ok:
        print("20 分钟内未恢复,退出", flush=True)
        return

    # ---- 恢复后立即执行 ----
    sid = '76561197960434622'
    print()
    print("=" * 70)
    print("[A] 愿望单/关注 API 复测")
    print("=" * 70)
    for path in [f'/IWishlistService/GetWishlist/v1/?steamid={sid}',
                 f'/IWishlistService/GetWishlistItemCount/v1/?steamid={sid}',
                 f'/IStoreService/GetGamesFollowed/v1/?steamid={sid}',
                 f'/IStoreService/GetGamesFollowedCount/v1/?steamid={sid}']:
        s, body, h, final = get(API + path)
        txt = body.decode('utf-8', 'replace')[:200].replace('\n', ' ')
        print(f"   {path.split('?')[0][:50]:50s} -> {s} {txt[:160]!r}")
        time.sleep(1)

    print()
    print("=" * 70)
    print("[B] 深度端点")
    print("=" * 70)
    cases = [
        (f'/IWishlistService/GetWishlistSortedFiltered/v1/?steamid={sid}', 'WishlistSortedFiltered'),
        ('/IPublishedFileService/GetUserVoteSummary/v1/?publishedfileids=1', 'UserVoteSummary'),
        ('/IPortal2Leaderboards_620/GetBucketizedData/v1/?leaderboardName=deaths_speedrun', 'P2Leaderboard'),
        ('/IContentServerDirectoryService/GetDepotPatchInfo/v1/?appid=570&depotid=570', 'DepotPatchInfo'),
        ('/IContentServerDirectoryService/GetCDNForVideo/v1/?property_type=3&client_ip=1.1.1.1', 'GetCDNForVideo'),
        ('/ISteamDirectory/GetSteamPipeDomains/v1/', 'SteamPipeDomains'),
        ('/ISteamBroadcast/PlayerStats/v1/', 'BroadcastPlayerStats'),
        ('/IAuthenticationService/GetAuthSessionInfo/v1/?client_id=0', 'GetAuthSessionInfo'),
        ('/IAuthenticationService/PollAuthSessionStatus/v1/?client_id=0&request_id=0', 'PollAuthSessionStatus'),
        ('/IAuthenticationService/GetPasswordRSAPublicKey/v1/?account_name=valve', 'RSA_valve'),
        ('/IAuthenticationService/GetPasswordRSAPublicKey/v1/?account_name=aaaaaaaaaaaaaaaaaaaa', 'RSA_rand'),
        ('/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=570', 'CurrentPlayers'),
        ('/IGCVersion_1046930/GetClientVersion/v1/', 'GC1046930'),
        ('/IGCVersion_1269260/GetClientVersion/v1/', 'GC1269260'),
        ('/IGCVersion_1422450/GetClientVersion/v1/', 'GC1422450'),
    ]
    for path, name in cases:
        s, body, h, final = get(API + path)
        txt = body.decode('utf-8', 'replace')[:200].replace('\n', ' ')
        print(f"   {name:22s} -> {s} {txt[:170]!r}")
        time.sleep(1)

    # 无 key 测试:GetSupportedAPIList 需要 key?试试
    print()
    print("=" * 70)
    print("[C] 网页端 wishlist 对照(steamcommunity)")
    print("=" * 70)
    for p in ['/wishlist/' + sid, '/id/valve']:
        s, body, h, final = get('https://steamcommunity.com' + p, timeout=20)
        txt = body.decode('utf-8', 'replace')
        title = re.search(r'<title>([^<]*)</title>', txt)
        print(f"   {p:40s} -> {s} len={len(body)} title={title.group(1)[:40] if title else ''!r}")
        time.sleep(1)


if __name__ == '__main__':
    main()
