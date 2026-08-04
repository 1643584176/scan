#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
API="https://api.steampowered.com"
SID="76561197960434622"

run() {
  local name="$1"; local url="$2"
  echo "=== $name ==="
  curl -s -m 20 -A "$UA" "$url" -w "\n[HTTP %{http_code} | %{size_download}B | %{time_total}s]\n" | head -c 500
  echo; echo
  sleep 1.5
}

echo "######################## [A] 深度 API 端点 ########################"
run WishlistSortedFiltered "$API/IWishlistService/GetWishlistSortedFiltered/v1/?steamid=$SID"
run GetGamesFollowedCount "$API/IStoreService/GetGamesFollowedCount/v1/?steamid=$SID"
run GetUserVoteSummary "$API/IPublishedFileService/GetUserVoteSummary/v1/?publishedfileids=1"
run P2Leaderboard "$API/IPortal2Leaderboards_620/GetBucketizedData/v1/?leaderboardName=deaths_speedrun"
run GetDepotPatchInfo "$API/IContentServerDirectoryService/GetDepotPatchInfo/v1/?appid=570&depotid=570"
run GetCDNForVideo "$API/IContentServerDirectoryService/GetCDNForVideo/v1/?property_type=3&client_ip=1.1.1.1"
run SteamPipeDomains "$API/ISteamDirectory/GetSteamPipeDomains/v1/"
run BroadcastPlayerStats "$API/ISteamBroadcast/PlayerStats/v1/"
run GetAuthSessionInfo0 "$API/IAuthenticationService/GetAuthSessionInfo/v1/?client_id=0"
run PollAuthSessionStatus "$API/IAuthenticationService/PollAuthSessionStatus/v1/?client_id=0&request_id=0"
run RSA_valve "$API/IAuthenticationService/GetPasswordRSAPublicKey/v1/?account_name=valve"
run RSA_rand "$API/IAuthenticationService/GetPasswordRSAPublicKey/v1/?account_name=aaaaaaaaaaaaaaaaaaaa"
run CurrentPlayers570 "$API/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=570"
run GC1046930 "$API/IGCVersion_1046930/GetClientVersion/v1/"
run GC1269260 "$API/IGCVersion_1269260/GetClientVersion/v1/"
run GC1422450 "$API/IGCVersion_1422450/GetClientVersion/v1/"
run GC730 "$API/IGCVersion_730/GetServerVersion/v1/"
run TFWorldStatus "$API/ITFSystem_440/GetWorldStatus/v1/"
run GetClientUpdateHosts "$API/IContentServerDirectoryService/GetClientUpdateHosts/v1/?cached_signature=0"
run GetServersForSteamPipe "$API/IContentServerDirectoryService/GetServersForSteamPipe/v1/?cell_id=0&max_servers=5"
run GetCMList "$API/ISteamDirectory/GetCMList/v1/?cellid=0&maxcount=3"

echo "######################## [B] steamcommunity 网页端对照 ########################"
run WEB_wishlist_gabe "https://steamcommunity.com/wishlist/$SID"
run WEB_id_valve "https://steamcommunity.com/id/valve"
run WEB_profile_valvetest "https://steamcommunity.com/profiles/76561198006409504"
run WEB_market "https://steamcommunity.com/market/"
