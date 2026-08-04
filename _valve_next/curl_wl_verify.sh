#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
API="https://api.steampowered.com"
COMM="https://steamcommunity.com"

echo "############ [0] gabe wishlist: 看 302 Location(不跟随)############"
curl -s -i -m 20 -A "$UA" "$COMM/wishlist/76561197960434622" 2>/dev/null | head -20
echo; sleep 1

echo "############ [1] 用户[6] 76561198092420573: 网页完整内容 ############"
curl -s -L --compressed -m 20 -A "$UA" "$COMM/wishlist/76561198092420573" -o /tmp/wl6.html -w "HTTP %{http_code} | %{size_download}B | final=%{url_effective}\n"
echo "--- title:"; grep -o '<title>[^<]*</title>' /tmp/wl6.html | head -1
echo "--- 关键文案:"; grep -io 'wishlist is [^<]\{0,60\}\|private[^<]\{0,40\}\|Friends Only\|sign in\|log in\|login' /tmp/wl6.html | sort | uniq -c | head -10
echo "--- data-appid 数: $(grep -c 'data-appid=' /tmp/wl6.html)"
echo "--- 页面内容前 800 字符:"; head -c 800 /tmp/wl6.html | tr -d '\n' | head -c 700
echo; echo; sleep 1

echo "############ [2] 再扫 15 个: API 非空优先,看网页 ############"
FOUND=0
for i in $(seq 1 15); do
  ACC=$(( (RANDOM * 32768 + RANDOM) % 400000000 + 2000000 ))
  SID=$(( 76561197960265728 + ACC ))
  A=$(curl -s -m 15 -A "$UA" "$API/IWishlistService/GetWishlist/v1/?steamid=$SID")
  CNT=$(echo "$A" | grep -o '"appid"' | wc -l)
  if [ "$CNIT" = "x" ]; then CNT=0; fi
  echo "[$i] $SID api_items=$CNT api=${A:0:70}"
  if [ "$CNT" -gt 0 ]; then
    W=$(curl -s -L --compressed -m 20 -A "$UA" "$COMM/wishlist/$SID" -w "|%{http_code}|%{url_effective}" 2>/dev/null)
    CODE=$(echo "$W" | awk -F'|' '{print $(NF-1)}')
    FINAL=$(echo "$W" | awk -F'|' '{print $NF}')
    echo "     WEB: code=$CODE final=$FINAL"
    FOUND=$((FOUND+1))
    if [ "$FOUND" -ge 3 ]; then break; fi
  fi
  sleep 1
done
