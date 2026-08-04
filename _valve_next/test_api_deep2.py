# -*- coding: utf-8 -*-
"""pt8: API 深度端点 + steamcommunity DNS/备用路径诊断"""
import json
import re
import sys
import ssl
import time
import socket
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
API = "https://api.steampowered.com"


def get(url, timeout=20, ua=UA):
    h = {'User-Agent': ua, 'Accept-Language': 'en-US,en;q=0.9'}
    r = urllib.request.Request(url, headers=h)
    try:
        resp = urllib.request.urlopen(r, context=CTX, timeout=timeout)
        return resp.status, resp.read(), dict(resp.headers), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers), e.geturl()
    except Exception as e:
        return 0, str(e).encode(), {}, ''


def main():
    # 0. DNS 解析诊断
    print("=" * 70)
    print("[0] DNS 解析诊断")
    print("=" * 70)
    for host in ['steamcommunity.com', 'api.steampowered.com',
                 'store.steampowered.com', 'www.playartifact.com']:
        try:
            ips = socket.getaddrinfo(host, 443, socket.AF_INET)
            ipset = sorted({x[4][0] for x in ips})
            print(f"   {host:28s} -> {ipset[:6]}")
        except Exception as e:
            print(f"   {host:28s} -> ERR {e}")
    time.sleep(0.5)

    # 1. api 可达性 + 深度端点
    print()
    print("=" * 70)
    print("[1] api.steampowered.com 深度端点")
    print("=" * 70)
    sid = '76561197960434622'
    cases = [
        # 深度愿望单(新端点,可能带隐私参数)
        (f'/IWishlistService/GetWishlistSortedFiltered/v1/?steamid={sid}', 'GetWishlistSortedFiltered'),
        (f'/IStoreService/GetGamesFollowedCount/v1/?steamid={sid}', 'GetGamesFollowedCount'),
        (f'/IWishlistService/GetWishlistItemCount/v1/?steamid={sid}', 'GetWishlistItemCount'),
        # 创意工坊投票(可枚举用户对物品的投票,需 publishedfileid)
        ('/IPublishedFileService/GetUserVoteSummary/v1/?publishedfileids=1', 'GetUserVoteSummary'),
        # Portal2 排行榜
        ('/IPortal2Leaderboards_620/GetBucketizedData/v1/?leaderboardName=deaths_speedrun', 'P2Leaderboard'),
        # 补丁信息枚举
        ('/IContentServerDirectoryService/GetDepotPatchInfo/v1/?appid=570&depotid=570', 'GetDepotPatchInfo'),
        ('/IContentServerDirectoryService/GetCDNForVideo/v1/?property_type=3&client_ip=1.1.1.1', 'GetCDNForVideo'),
        # SteamPipe 域
        ('/ISteamDirectory/GetSteamPipeDomains/v1/', 'GetSteamPipeDomains'),
        # 广播
        ('/ISteamBroadcast/PlayerStats/v1/', 'BroadcastPlayerStats'),
        # 认证会话信息(client_id 枚举?)
        ('/IAuthenticationService/GetAuthSessionInfo/v1/?client_id=0', 'GetAuthSessionInfo'),
        ('/IAuthenticationService/PollAuthSessionStatus/v1/?client_id=0&request_id=0', 'PollAuthSessionStatus'),
        # RSA 公钥(用户名枚举:区别响应)
        ('/IAuthenticationService/GetPasswordRSAPublicKey/v1/?account_name=valve', 'RSA_valve'),
        ('/IAuthenticationService/GetPasswordRSAPublicKey/v1/?account_name=aaaaaaaaaaaaaaaaaaaa', 'RSA_rand'),
        # 玩家数量(任意 appid)
        ('/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=570', 'CurrentPlayers'),
        # 未发布 appid 版本
        ('/IGCVersion_1046930/GetClientVersion/v1/', 'GC1046930'),
    ]
    for path, name in cases:
        s, body, h, final = get(API + path)
        txt = body.decode('utf-8', 'replace')[:220].replace('\n', ' ')
        print(f"   {name:28s} -> {s} {txt[:190]!r}")
        time.sleep(0.7)

    # 2. steamcommunity 备用路径
    print()
    print("=" * 70)
    print("[2] steamcommunity 备用路径(steamstatic 等)")
    print("=" * 70)
    for url in ['https://steamcommunity-a.akamaihd.net/',
                'https://community.cloudflare.steamstatic.com/',
                'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb.jpg',
                ]:
        s, body, h, final = get(url, timeout=15)
        print(f"   {url[:70]:70s} -> {s} len={len(body)}")
        time.sleep(0.5)


if __name__ == '__main__':
    main()
