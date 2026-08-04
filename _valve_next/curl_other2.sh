#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
API="https://api.steampowered.com"
SID="76561197960434622"

run() {
  local name="$1"; local url="$2"
  echo "=== $name ==="
  curl -s -m 20 -A "$UA" "$url" -w "\n[HTTP %{http_code} | %{size_download}B]\n" | head -c 500
  echo; echo
  sleep 1.2
}

echo "############ [A] 游戏库/徽章/成就 XML(steamcommunity 未登录面) ############"
run GAMES_XML "https://steamcommunity.com/profiles/$SID/games?tab=all&xml=1"
run GAMES_XML2 "https://steamcommunity.com/profiles/76561198092420573/games?tab=all&xml=1"
run BADGES_XML "https://steamcommunity.com/profiles/$SID/badges?xml=1"
run GROUPS_XML "https://steamcommunity.com/profiles/$SID/groups?xml=1"
run STATS_XML "https://steamcommunity.com/profiles/$SID/stats/570?xml=1"

echo "############ [B] API 公开接口补充 ############"
run GetServerInfo "$API/ISteamWebAPIUtil/GetServerInfo/v1/"
run GetServerList "$API/IGameServersService/GetServerList/v1/?filter=appid\\570"
run GetServerList0 "$API/IGameServersService/GetServerList/v1/?filter=appid\\570&limit=3"
run UpToDateCheck "$API/ISteamApps/UpToDateCheck/v1/?appid=570&version=1"

echo "############ [C] 创意工坊公开查询(POST) ############"
echo "=== GetPublishedFileDetails (POST, 公开文件) ==="
curl -s -m 20 -A "$UA" -X POST "$API/ISteamRemoteStorage/GetPublishedFileDetails/v1/" -d "itemcount=1&publishedfileids%5B0%5D=2904657146" -w "\n[HTTP %{http_code}]\n" | head -c 800
echo; echo

echo "############ [D] linkfilter 精确 Location ############"
echo "--- 未登录 ---"
curl -s -D - -o /dev/null -m 15 -A "$UA" "https://steamcommunity.com/linkfilter/?url=https%3A%2F%2Fexample.com" | grep -iE "^HTTP|^Location"
echo "--- javascript: payload ---"
curl -s -D - -o /dev/null -m 15 -A "$UA" "https://steamcommunity.com/linkfilter/?url=javascript%3Aalert(1)" | grep -iE "^HTTP|^Location"
