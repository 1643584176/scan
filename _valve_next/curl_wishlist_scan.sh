#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
API="https://api.steampowered.com"
COMM="https://steamcommunity.com"

echo "############ [0] 跟随重定向: gabe 愿望单 ############"
curl -s -L --compressed -m 25 -A "$UA" "$COMM/wishlist/76561197960434622" -o /tmp/wl_gabe.html -w "HTTP %{http_code} | %{size_download}B | %{url_effective}\n"
grep -o '<title>[^<]*</title>' /tmp/wl_gabe.html | head -2
echo "data-appid 数: $(grep -c 'data-appid=' /tmp/wl_gabe.html)"
grep -io 'wishlist is [a-z ]*\|friends only\|private' /tmp/wl_gabe.html | sort | uniq -c | head -5
echo
sleep 1

echo "############ [1] 扫描 30 个随机 steamid(网页 vs API)############"
for i in $(seq 1 30); do
  ACC=$(( (RANDOM * 32768 + RANDOM) % 300000000 + 1000000 ))
  SID=$(( 76561197960265728 + ACC ))
  # 网页
  W=$(curl -s -L --compressed -m 20 -A "$UA" "$COMM/wishlist/$SID" -w "|%{http_code}" 2>/dev/null)
  CODE=${W##*|}
  HTML=${W%|*}
  PRIV=$(echo "$HTML" | grep -ic 'wishlist is private\|friends only\|wishlist is currently private')
  ITEMS=$(echo "$HTML" | grep -c 'data-appid=')
  # API
  A=$(curl -s -m 15 -A "$UA" "$API/IWishlistService/GetWishlist/v1/?steamid=$SID")
  APICNT=$(echo "$A" | grep -o '"appid"' | wc -l)
  echo "[$i] $SID web=$CODE priv=$PRIV items=$ITEMS api_count=$APICNT api=${A:0:60}"
  if [ "$CODE" != "200" ]; then echo "     WEB CODE=$CODE"; fi
  sleep 1
done

echo
echo "############ [2] 对照: 无效 steamid ############"
for SID in 1 76561197960265728 99999999999999999; do
  echo "--- steamid=$SID"
  curl -s -m 15 -A "$UA" "$API/IWishlistService/GetWishlist/v1/?steamid=$SID" | head -c 200
  echo
  sleep 0.5
done
