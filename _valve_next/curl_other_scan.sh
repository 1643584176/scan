#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
API="https://api.steampowered.com"
SID="76561197960434622"

run() {
  local name="$1"; local url="$2"
  echo "=== $name ==="
  curl -s -m 20 -A "$UA" "$url" -w "\n[HTTP %{http_code} | %{size_download}B | %{time_total}s]\n" | head -c 600
  echo; echo
  sleep 1.5
}

echo "################ [A] IPlayerService 系列(未测) ################"
run GetOwnedGames "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?steamid=$SID&include_appinfo=true&include_played_free_games=true&format=json"
run GetSteamLevel "$API/IPlayerService/GetSteamLevel/v1/?steamid=$SID"
run GetBadges "$API/IPlayerService/GetBadges/v1/?steamid=$SID"
run GetRecentlyPlayedGames "$API/IPlayerService/GetRecentlyPlayedGames/v1/?steamid=$SID&count=5"
run GetCommunityBadgeProgress "$API/IPlayerService/GetCommunityBadgeProgress/v1/?steamid=$SID&badgeid=1"

echo "################ [B] ISteamUser 系列(未测) ################"
run GetPlayerSummaries "$API/ISteamUser/GetPlayerSummaries/v2/?steamids=$SID"
run GetFriendList "$API/ISteamUser/GetFriendList/v1/?steamid=$SID"
run GetPlayerBans "$API/ISteamUser/GetPlayerBans/v1/?steamids=$SID"
run GetUserGroupList "$API/ISteamUser/GetUserGroupList/v1/?steamid=$SID"

echo "################ [C] 其他接口(未测) ################"
run GetAppList "$API/ISteamApps/GetAppList/v2/?limit=5"
run GetNewsForApp "$API/ISteamNews/GetNewsForApp/v2/?appid=570&count=3"
run GlobalAchievPercent "$API/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/?gameid=570"
run GetSchemaForGame "$API/ISteamUserStats/GetSchemaForGame/v2/?appid=570"
run GetPlayerAchievements "$API/ISteamUserStats/GetPlayerAchievements/v1/?appid=570&steamid=$SID"
run GetUserStatsForGame "$API/ISteamUserStats/GetUserStatsForGame/v2/?appid=570&steamid=$SID"
run GetOwnedGamesNoKey "$API/IPlayerService/GetOwnedGames/v1/?steamid=76561198092420573&include_appinfo=true"

echo "################ [D] playartifact.com 重试 ################"
run ArtifactHome "https://www.playartifact.com/"
run ArtifactAPI "https://api.playartifact.com/"
echo "=== artifact DNS ==="
nslookup www.playartifact.com 2>&1 | head -8

echo "################ [E] steamcommunity linkfilter / XML ################"
run Linkfilter "https://steamcommunity.com/linkfilter/?url=https%3A%2F%2Fexample.com"
run XMLProfile "https://steamcommunity.com/profiles/$SID?xml=1"
run XMLFriends "https://steamcommunity.com/profiles/$SID/friends?xml=1"
run SearchUsers "https://steamcommunity.com/actions/SearchUsers?term=gabe&l=english"
