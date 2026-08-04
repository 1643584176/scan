#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
API="https://api.steampowered.com"
BASE=76561197960265728

# 2021-2024 注册区间随机 accountid(158M-175M),逐个确认 profile 存在后再测 API
ACCTS="158300000 159000000 161200000 164500000 167800000 170000000 172500000 174000000"

for A in $ACCTS; do
  SID=$((BASE + A))
  TITLE=$(curl -s -m 15 -A "$UA" "https://steamcommunity.com/profiles/$SID" | grep -o '<title>[^<]*</title>' | head -1)
  if echo "$TITLE" | grep -q "Error"; then
    echo "  $SID (acct $A): 不存在,跳过"
    continue
  fi
  echo "  $SID (acct $A): $TITLE"
  echo -n "     GetWishlistItemCount: "
  curl -s -m 15 -A "$UA" "$API/IWishlistService/GetWishlistItemCount/v1/?steamid=$SID"
  echo
  echo -n "     GetGamesFollowed: "
  curl -s -m 15 -A "$UA" "$API/IStoreService/GetGamesFollowed/v1/?steamid=$SID" | head -c 120
  echo
  sleep 0.8
done

echo
echo "=== 对照:2004 老账号 gabe(旧默认公开) ==="
curl -s -m 15 -A "$UA" "$API/IWishlistService/GetWishlistItemCount/v1/?steamid=76561197960434622"
echo
