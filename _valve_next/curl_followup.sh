#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

echo "=== [1] Linkfilter Location 头 ==="
curl -s -I -m 15 -A "$UA" "https://steamcommunity.com/linkfilter/?url=https%3A%2F%2Fexample.com"
echo; echo "--- 带 cookie 跟随(模拟已登录用户点外部链接) ---"
curl -s -I -m 15 -A "$UA" -H "Cookie: steamLoginSecure=xxx" "https://steamcommunity.com/linkfilter/?url=https%3A%2F%2Fexample.com"

echo; echo "=== [2] linkfilter 其他 payload ==="
curl -s -I -m 15 -A "$UA" "https://steamcommunity.com/linkfilter/?url=https%3A%2F%2Fevil.com%2Fx"
curl -s -I -m 15 -A "$UA" "https://steamcommunity.com/linkfilter/?url=javascript:alert(1)"
curl -s -I -m 15 -A "$UA" "https://steamcommunity.com/linkfilter/?url=//evil.com"
curl -s -I -m 15 -A "$UA" "https://steamcommunity.com/linkfilter/?url=https://steamcommunity.com%2F@evil.com"

echo; echo "=== [3] playartifact 302 Location ==="
curl -s -I -m 15 -A "$UA" "https://www.playartifact.com/"
curl -s -I -m 15 -A "$UA" "https://playartifact.com/"

echo; echo "=== [4] SearchUsers 302 Location ==="
curl -s -I -m 15 -A "$UA" "https://steamcommunity.com/actions/SearchUsers?term=gabe&l=english"

echo; echo "=== [5] XML 私密用户对照(随机私密 profile) ==="
curl -s -m 15 -A "$UA" "https://steamcommunity.com/profiles/76561198092420573?xml=1" | head -c 800
echo; echo
curl -s -m 15 -A "$UA" "https://steamcommunity.com/profiles/76561198092420573" | grep -o '<title>[^<]*</title>'

echo; echo "=== [6] GetAppList 正确路径 ==="
curl -s -m 20 -A "$UA" "https://api.steampowered.com/ISteamApps/GetAppList/v2/" -w "\n[HTTP %{http_code}]\n" | head -c 300
