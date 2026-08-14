# -*- coding: utf-8 -*-
"""MCP 完整方法探测:catalog.shopify.com/api/ucp/mcp"""
from curl_cffi import requests

PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}

url = "https://catalog.shopify.com/api/ucp/mcp"
tests = [
    ("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}),
    ("ping", {}),
    ("resources/list", {}),
    ("resources/templates/list", {}),
    ("prompts/list", {}),
    ("tools/list", {}),
    ("logging/setLevel", {"level": "debug"}),
    ("completion/complete", {"ref": {"type": "ref/prompt", "name": "x"}, "argument": {"name": "x", "value": "y"}}),
]
for method, params in tests:
    body = {"jsonrpc": "2.0", "method": method, "id": 1, "params": params}
    try:
        r = requests.post(url, json=body, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
        print(f"[{method}] HTTP {r.status_code}")
        print(f"  {r.text[:400]}")
    except Exception as e:
        print(f"[{method}] ERROR {e}")
