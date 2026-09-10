# -*- coding: utf-8 -*-
"""ET59b: no-session reachability triage on 40 read-query webroutes (full output)"""
import ssl, http.client, time

CANDS = [
    "/webroutes/location/search", "/webroutes/location/locationGeoData", "/webroutes/location/get",
    "/webroutes/reviews/loadMore", "/webroutes/reviews/sortReviews", "/webroutes/reviews/suggestTags",
    "/webroutes/reviews/comment/loadMore", "/webroutes/photos/loadMore", "/webroutes/photos/viewGallery",
    "/webroutes/menu/viewMenu", "/webroutes/restaurant/info", "/webroutes/restaurant/getHygieneDetails",
    "/webroutes/restaurant/getHyperpureDetails", "/webroutes/restaurant/userModalInfo",
    "/webroutes/order/receipt", "/webroutes/order/details", "/webroutes/cdng/getDiningCart",
    "/webroutes/cdng/fetchQRData", "/webroutes/cdng/getCallServerState", "/webroutes/feeding/getTotalAmount",
    "/webroutes/getPage", "/webroutes/kitchen/city", "/webroutes/promo/info", "/webroutes/awards/winners/",
    "/webroutes/loyaltyqrscan/getResList", "/webroutes/home/quickLinks", "/webroutes/home/o2quickLinks",
    "/webroutes/blog/posts", "/webroutes/ads", "/webroutes/hygiene", "/webroutes/dote/home",
    "/webroutes/dote/cart", "/webroutes/dote/address", "/webroutes/dote/orderDetails",
    "/webroutes/gift/getCrystalData", "/webroutes/orderShare/getCrystalData", "/webroutes/postCdng/getOrderDetails",
    "/webroutes/postOrder/crystalPromoCard", "/webroutes/postOrder/getRiderStatus", "/webroutes/postOrder/pollCrystalData",
]

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"

def get(path):
    try:
        conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=12, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "application/json,*/*",
                     "X-Hackerone": "xxbo", "Referer": "https://www.zomato.com/ncr/restaurants?q=pizza"})
        r = conn.getresponse()
        raw = r.read(4000)
        conn.close()
        body = raw.decode("utf-8", "replace")[:130].replace("\n", " ")
        print("[%d] %-52s %s" % (r.status, path[:52], body), flush=True)
    except Exception as e:
        print("[EXC] %-52s %s" % (path[:52], repr(e)[:80]), flush=True)

for p in CANDS:
    get(p)
    time.sleep(0.7)
print("done %d" % len(CANDS), flush=True)
