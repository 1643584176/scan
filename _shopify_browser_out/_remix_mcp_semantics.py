# -*- coding: utf-8 -*-
"""1) Remix .data 资源路由绕过(shop.app /agents/*)
2) MCP 协议标准方法探测(catalog.shopify.com)
3) by-shopify-id 参数语义分析(500 行为差异)
"""
from curl_cffi import requests

PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Content-Type": "application/json",
}

def remix_data_probe():
    print("== Remix .data 路由探测(shop.app) ==")
    paths = [
        "/agents/orders.data",
        "/agents/search.data",
        "/agents/orderSearch.data",
        "/agents/orders/by-shopify-id.data?shopifyOrderId=1102015168554",
        "/agents/auth/device-code.data",
        "/agents/auth/token.data",
        "/agents/auth/userinfo.data",
        "/agents/returns.data",
        "/web/api/available-feature-flags.data",
        "/agents/search.data?query=test",
        "/agents/orders.data?type=recent",
    ]
    for p in paths:
        url = "https://shop.app" + p
        try:
            r = requests.get(url, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
            print(f"[GET {p[:60]}] HTTP {r.status_code} len={len(r.text)} | {r.text[:130]}")
        except Exception as e:
            print(f"[GET {p[:60]}] ERROR {e}")

def mcp_method_probe():
    print("\n== MCP 标准方法探测(catalog.shopify.com/api/ucp/mcp) ==")
    url = "https://catalog.shopify.com/api/ucp/mcp"
    methods = [
        ("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}),
        ("ping", {}),
        ("resources/list", {}),
        ("prompts/list", {}),
        ("tools/call", {"name": "search_catalog", "arguments": {"query": "shoes"}}),
        ("tools/call", {"name": "lookup_catalog", "arguments": {"id": "gid://shopify/ProductVariant/50362300006715"}}),
        ("tools/list", {}),
    ]
    for method, params in methods:
        body = {"jsonrpc": "2.0", "method": method, "id": 1, "params": params}
        try:
            r = requests.post(url, json=body, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
            print(f"[{method}] HTTP {r.status_code} | {r.text[:250]}")
        except Exception as e:
            print(f"[{method}] ERROR {e}")

def by_shopify_id_semantics():
    print("\n== by-shopify-id 参数语义 ==")
    vals = [
        "1102015168554",        # 基线(草稿 ID)
        "0", "1", "-1", "999999999999999999999",  # 边界
        "gid://shopify/Order/1102015168554",
        "gid://shopify/DraftOrder/1102015168554",
        "1102015168554.0", "1e12", "0x100", "+1102015168554",
        "1102015168554%00", "1102015168554%20",
        " 1102015168554",
    ]
    for v in vals:
        url = "https://shop.app/agents/orders/by-shopify-id?shopifyOrderId=" + v
        try:
            r = requests.get(url, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
            print(f"[{v!r:45s}] HTTP {r.status_code} | {r.text[:150]}")
        except Exception as e:
            print(f"[{v!r:45s}] ERROR {e}")

if __name__ == "__main__":
    remix_data_probe()
    mcp_method_probe()
    by_shopify_id_semantics()
