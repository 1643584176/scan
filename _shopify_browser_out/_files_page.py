# -*- coding: utf-8 -*-
"""从 admin Files 页面提取 fileCreate/stagedUploadsCreate persisted query hash"""
import re, json, time
from curl_cffi import requests

COOKIE_FILE = r"C:\Users\tndc2\AppData\Local\Temp\admin_cookies.txt"
PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}

def load_cookies():
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    return {k: v for k, v in (p.split("=", 1) for p in raw.split("; ") if "=" in p)}

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Origin": "https://admin.shopify.com",
}

def get_page():
    r = requests.get("https://admin.shopify.com/store/jqpkdm-kb/settings/files", headers=H, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=40)
    print(f"[page] HTTP {r.status_code} len={len(r.text)}")
    # 提取 csrf token
    m = re.search(r'"csrfToken"\s*:\s*"([^"]+)"', r.text)
    if m:
        print(f"[csrf] {m.group(1)}")
    # 提取 JS 入口
    srcs = re.findall(r'(?:src|href)="([^"]+\.js[^"]*)"', r.text)
    for s in srcs[:10]:
        print(f"[js] {s}")
    return r.text

if __name__ == "__main__":
    html = get_page()
    open(r"D:\scan\_shopify_browser_out\files_page.html", "w", encoding="utf-8").write(html)
