# -*- coding: utf-8 -*-
"""尝试用 PayPal 网关完成草稿订单(DraftOrderComplete)"""
import json, sys, time
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

URL = "https://admin.shopify.com/api/operations/12af77c8135a10656e3cf14cb69d746505a1df3b62c08faea80a0a3949c21f8d/DraftOrderComplete/shopify/jqpkdm-kb"

def complete(gateway_id, label):
    body = {
        "operationName": "DraftOrderComplete",
        "variables": {
            "id": "gid://shopify/DraftOrder/1102015168554",
            "paymentPending": True,
            "paymentGatewayId": gateway_id,
            "sourceName": "shopify_draft_orders",
            "bypassCartValidations": False,
        },
        "extensions": {
            "client_context": {
                "page_view_token": "81a384a6-1a26-4f04-93a2-faca565b1f40",
                "client_route_handle": "draftOrders:show",
                "client_pathname": "/store/jqpkdm-kb/draft_orders/1102015168554",
                "client_normalized_pathname": "/store/:storeHandle/draft_orders/:id",
                "shopify_session_token": "0f6832a6-1f3c-40ef-805e-29f861ec7367",
                "shopify_multitrack_token": "34b29e38-9809-47b2-ac03-64535d399fdd",
            }
        },
    }
    r = requests.post(URL, json=body, headers=HEADERS, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=40)
    print(f"[{label}] HTTP {r.status_code}")
    txt = r.text
    print(txt[:2000])
    return r

if __name__ == "__main__":
    # 1) PayPal 网关
    r = complete("gid://shopify/PaymentGateway/97109245994", "PAYPAL")
    time.sleep(1)
    # 2) Shopify Payments 网关(上次 null 失败,试试显式 id)
    r2 = complete("gid://shopify/PaymentGateway/97109278762", "SHOPIFY_PAYMENTS")
