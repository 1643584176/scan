# -*- coding: utf-8 -*-
"""抓 draft_orders 页面,解析 server-data 里的 chunk 预加载清单"""
import re, json
from curl_cffi import requests

COOKIE_FILE = r"C:\Users\tndc2\AppData\Local\Temp\admin_cookies.txt"
PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}

def load_cookies():
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    return {k: v for k, v in (p.split("=", 1) for p in raw.split("; ") if "=" in p)}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-CH-UA": '"Chromium";v="138", "Google Chrome";v="138", "Not.A/Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

for path in ["/store/jqpkdm-kb/draft_orders/1102015168554", "/store/jqpkdm-kb/draft_orders"]:
    url = "https://admin.shopify.com" + path
    r = requests.get(url, headers=HEADERS, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=40)
    print(f"### {path} HTTP {r.status_code} len={len(r.text)}")
    html = r.text
    open(rf"C:\Users\tndc2\AppData\Local\Temp\do_{path.split('/')[-1][:20]}.html", "w", encoding="utf-8").write(html)
    # 找 server-data / 模块清单
    for pat in [r'"modulepreload"[^>]*', r'server-data[^>]*', r'\.js"', r'assets/[a-zA-Z0-9_.-]+\.js']:
        m = re.findall(pat, html)
        if m:
            print(f"  [{pat[:20]}] {len(m)} matches")
            for x in m[:15]:
                print("   ", x[:200])
    print()
