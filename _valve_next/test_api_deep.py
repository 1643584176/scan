# -*- coding: utf-8 -*-
"""pt4: api.steampowered.com 深入 - 免 key 端点批量实测"""
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


def get(url, timeout=20):
    h = {'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'}
    r = urllib.request.Request(url, headers=h)
    try:
        resp = urllib.request.urlopen(r, context=CTX, timeout=timeout)
        return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except Exception as e:
        return 0, str(e).encode(), {}


def main():
    tests = [
        # (path, 说明)
        ('/IContentServerDirectoryService/GetDepotPatchInfo/v1/?appid=570&depotid=571&source_manifestid=1&target_manifestid=2',
         'depot patch 信息(旧manifest)'),
        ('/IContentServerDirectoryService/GetDepotPatchInfo/v1/?appid=730&depotid=2347771&source_manifestid=1&target_manifestid=2',
         'depot patch CS2'),
        ('/ISteamApps/GetSDRConfig/v1/?appid=570', 'SDR 配置'),
        ('/ISteamApps/GetSDRConfig/v1/?appid=730', 'SDR 配置 CS2'),
        ('/IContentServerDirectoryService/GetServersForSteamPipe/v1/?cell_id=0&max_servers=5',
         'SteamPipe 服务器列表'),
        ('/IContentServerDirectoryService/GetCDNForVideo/v1/?property_type=1&client_ip=8.8.8.8&client_region=US',
         '视频 CDN 分配'),
        ('/IContentServerDirectoryService/GetClientUpdateHosts/v1/', '客户端更新主机'),
        ('/IContentServerDirectoryService/GetClientUpdateHosts/v1/?cached_signature=', '客户端更新主机(空sig)'),
        ('/IContentServerDirectoryService/PickSingleContentServer/v1/?property_type=1&cell_id=0&client_ip=8.8.8.8',
         '内容服务器选择'),
        ('/ISteamDirectory/GetCMListForConnect/v1/?cellid=0&maxcount=3', 'CM 连接列表'),
        ('/ISteamDirectory/GetSteamPipeDomains/v1/', 'SteamPipe 域名'),
        ('/IPublishedFileService/GetUserVoteSummary/v1/?publishedfileids=1', '创意工坊投票(需key?)'),
        ('/IGCVersion_570/GetServerVersion/v1/', 'Dota2 服务器版本'),
        ('/IGCVersion_730/GetServerVersion/v1/', 'CS2 服务器版本'),
        ('/IGCVersion_440/GetServerVersion/v1/', 'TF2 服务器版本'),
        ('/IGCVersion_1046930/GetClientVersion/v1/', '游戏1046930 客户端版本'),
        ('/IGCVersion_1269260/GetClientVersion/v1/', '游戏1269260 客户端版本'),
        ('/IGCVersion_1422450/GetClientVersion/v1/', '游戏1422450 客户端版本'),
        ('/ITFSystem_440/GetWorldStatus/v1/', 'TF2 世界状态'),
        ('/ISteamBroadcast/PlayerStats/v1/', '广播玩家统计'),
        ('/IStoreService/GetGamesFollowed/v1/?steamid=76561197960434622', '关注的游戏(需key?)'),
        ('/IWishlistService/GetWishlist/v1/?steamid=76561197960434622', '愿望单(未登录?)'),
        ('/IWishlistService/GetWishlistItemCount/v1/?steamid=76561197960434622', '愿望单数量(未登录?)'),
        ('/IStoreService/GetRecommendedTagsForUser/v1/?language=english&country_code=US', '推荐标签'),
        ('/ISteamUserStats/GetGlobalStatsForGame/v1/?appid=570&count=1&name[0]=total_players',
         '全球统计'),
        ('/ISteamRemoteStorage/GetCollectionDetails/v1/', '合集详情(POST)'),
        ('/ISteamUserOAuth/GetTokenDetails/v1/?access_token=', 'token 详情(空token)'),
        ('/IAuthenticationService/GetAuthSessionInfo/v1/?client_id=1', '认证会话信息'),
        ('/IAuthenticationService/GetPasswordRSAPublicKey/v1/?account_name=test', 'RSA 公钥'),
    ]
    for path, desc in tests:
        method = 'POST' if 'GetCollectionDetails' in path else 'GET'
        try:
            if method == 'GET':
                s, body, h = get(API + path)
            else:
                data = b'collectioncount=1&publishedfileids[0]=1'
                req = urllib.request.Request(API + path, data=data,
                                             headers={'User-Agent': UA})
                resp = urllib.request.urlopen(req, context=CTX, timeout=20)
                s, body = resp.status, resp.read()
        except urllib.error.HTTPError as e:
            s, body = e.code, e.read()
        except Exception as e:
            s, body = 0, str(e).encode()
        txt = body.decode('utf-8', 'replace')[:220].replace('\n', ' ')
        print(f"{s} {desc:28s} {path[:60]:60s}")
        print(f"   {txt[:180]!r}")
        time.sleep(0.6)


if __name__ == '__main__':
    main()
