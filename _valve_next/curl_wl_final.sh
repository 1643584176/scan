#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
API="https://api.steampowered.com"
SID="76561197960434622"

echo "=== [1] GetWishlistSortedFiltered 带 context/data_request ==="
curl -s -m 20 -A "$UA" "$API/IWishlistService/GetWishlistSortedFiltered/v1/?steamid=$SID&context=%7B%22steamid%22%3A%22$SID%22%7D&data_request=%7B%22wishlist_basic%22%3Atrue%7D" -w "\n[HTTP %{http_code} | %{size_download}B]\n" | head -c 700
echo; echo; sleep 1

echo "=== [2] GetWishlistItemCount(3 个不同用户) ==="
for X in 76561197960434622 76561198092420573 99999999999999999; do
  echo -n "  $X -> "
  curl -s -m 15 -A "$UA" "$API/IWishlistService/GetWishlistItemCount/v1/?steamid=$X"
  echo
  sleep 0.5
done
echo; echo

echo "=== [3] GetGamesFollowed 完整(前 2 个用户) ==="
for X in 76561197960434622 76561198092420573; do
  echo "  $X ->"
  curl -s -m 15 -A "$UA" "$API/IStoreService/GetGamesFollowed/v1/?steamid=$X" | head -c 400
  echo; echo
  sleep 0.5
done
