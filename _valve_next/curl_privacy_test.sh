#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
API="https://api.steampowered.com"

# accountid 高位 = 注册时间更晚(2021+ 注册,愿望单默认私密)
# 76561197960265728 + accountid
# 老账号对照:gabe(168894, ~2004)
# 新账号:accountid 160M-190M 范围随机(2021-2025 注册)
NEW_IDS="76561198160000000 76561198170000000 76561198180000000 76561198190000000 76561198200000000"

echo "############ [A] 新账号(2021+ 注册,愿望单默认私密):API 是否仍返回数据? ############"
for X in $NEW_IDS; do
  echo "--- steamid=$X ---"
  echo -n "  GetWishlist     : "
  curl -s -m 15 -A "$UA" "$API/IWishlistService/GetWishlist/v1/?steamid=$X" | head -c 300
  echo
  echo -n "  GetWishlistItemCount: "
  curl -s -m 15 -A "$UA" "$API/IWishlistService/GetWishlistItemCount/v1/?steamid=$X" | head -c 150
  echo
  echo -n "  GetGamesFollowed: "
  curl -s -m 15 -A "$UA" "$API/IStoreService/GetGamesFollowed/v1/?steamid=$X" | head -c 200
  echo
  echo -n "  WEB wishlist    : "
  curl -s -o /dev/null -D - -m 15 -A "$UA" "https://steamcommunity.com/wishlist/$X" | grep -iE "^HTTP|^Location" | tr -d '\r' | paste -sd' '
  echo -n "  WEB profile     : "
  curl -s -m 15 -A "$UA" "https://steamcommunity.com/profiles/$X" | grep -o '<title>[^<]*</title>' | head -1
  echo
  sleep 1
done

echo "############ [B] GetWishlist 响应结构(是否含 privacy 字段) ############"
curl -s -m 15 -A "$UA" "$API/IWishlistService/GetWishlist/v1/?steamid=76561197960434622" -w "\n[HTTP %{http_code}]\n" | head -c 400

echo
echo "############ [C] 老账号对照(2018 前注册,旧默认公开) ############"
echo -n "  gabe GetWishlistItemCount: "
curl -s -m 15 -A "$UA" "$API/IWishlistService/GetWishlistItemCount/v1/?steamid=76561197960434622"
echo
echo -n "  valve(76561197960435530) GetWishlist: "
curl -s -m 15 -A "$UA" "$API/IWishlistService/GetWishlist/v1/?steamid=76561197960435530" | head -c 200
echo
