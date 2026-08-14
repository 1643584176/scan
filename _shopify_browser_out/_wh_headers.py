# -*- coding: utf-8 -*-
"""webhook.site 自定义响应头实验:找能设置 Cache-Control: public 的配置方式
候选:headers / default_headers / actions
"""
import json, time
from curl_cffi import requests

PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
UUID = "3527a249-5beb-4849-ab04-5954d8194531"
TOKEN_URL = f"https://webhook.site/token/{UUID}"
WH_URL = f"https://webhook.site/{UUID}"

def try_config(label, cfg):
    try:
        r = requests.put(TOKEN_URL, json=cfg, headers=H, proxies=PROXY, impersonate="chrome", timeout=20)
        print(f"[{label} PUT] HTTP {r.status_code} | {r.text[:200]}")
    except Exception as e:
        print(f"[{label} PUT] ERROR {e}")
    time.sleep(1)
    try:
        r = requests.get(WH_URL, headers=H, proxies=PROXY, impersonate="chrome", timeout=20)
        print(f"[{label} GET]  HTTP {r.status_code} cc={r.headers.get('Cache-Control')} ct={r.headers.get('Content-Type')}")
        print(f"   body: {r.text[:120]}")
    except Exception as e:
        print(f"[{label} GET]  ERROR {e}")

if __name__ == "__main__":
    # 基线
    try_config("baseline", {"default_status": 200, "default_content": '{"ucp":{"version":"2026-04-08"}}', "default_content_type": "application/json"})
    # 尝试 headers 字段
    try_config("headers", {"default_status": 200, "default_content": '{"ucp":{"version":"2026-04-08"}}', "default_content_type": "application/json", "headers": {"Cache-Control": "public, max-age=3600"}})
    # 尝试 default_headers
    try_config("default_headers", {"default_status": 200, "default_content": '{"ucp":{"version":"2026-04-08"}}', "default_content_type": "application/json", "default_headers": {"Cache-Control": "public, max-age=3600"}})
    # 尝试 actions(set-response)
    try_config("actions", {"default_status": 200, "default_content": '{"ucp":{"version":"2026-04-08"}}', "default_content_type": "application/json", "actions": [{"action": "set-response", "response": {"status": 200, "content": '{"ucp":{"version":"2026-04-08"}}', "content_type": "application/json", "headers": {"Cache-Control": "public, max-age=3600"}}}]})
