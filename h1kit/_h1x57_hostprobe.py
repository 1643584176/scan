# -*- coding: utf-8 -*-
"""CSP 泄漏 host + api.hackerone.com 匿名探测(2026-09-08)
目标:找主站之外与报告数据相关的独立权限面
"""
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA})

TARGETS = [
    # (label, url, method)
    ("api_reports_tgt", "https://api.hackerone.com/v1/reports/3732660", "GET"),
    ("api_reports_own", "https://api.hackerone.com/v1/reports/3992341", "GET"),
    ("api_root", "https://api.hackerone.com/", "GET"),
    ("api_v1_root", "https://api.hackerone.com/v1/", "GET"),
    ("api_me", "https://api.hackerone.com/v1/me", "GET"),
    ("chat_agent_root", "https://chat-agent.hackerone.com/", "GET"),
    ("chat_agent_health", "https://chat-agent.hackerone.com/health", "GET"),
    ("ext_content", "https://a5s.hackerone-ext-content.com/", "GET"),
    ("integ_conf", "https://hackerone.integration-configuration.com/", "GET"),
    ("errors_net", "https://errors.hackerone.net/", "GET"),
]

for label, url, method in TARGETS:
    try:
        r = S.request(method, url, timeout=12, allow_redirects=False)
        hdrs = {k: v for k, v in r.headers.items()
                if k.lower() in ("content-type", "server", "cf-ray", "cf-cache-status", "location", "www-authenticate", "allow", "x-frame-options")}
        body = r.text[:200].replace("\n", " ")
        print(f"== {label} -> {r.status_code} {r.reason} | {hdrs}")
        print(f"   body: {body}")
    except Exception as e:
        print(f"== {label} -> ERR {type(e).__name__}: {e}")
