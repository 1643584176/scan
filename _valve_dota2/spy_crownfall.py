# -*- coding: utf-8 -*-
"""捕获 /crownfall 活动页的 API 请求(懒加载 chunk 可能含专属 API)"""
import time
from playwright.sync_api import sync_playwright

reqs = []
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True, args=["--no-proxy-server"])
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    def on_req(r):
        u = r.url
        if any(k in u for k in (".js", ".css", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".woff", ".ico", ".gif", ".mp4", ".webm")):
            return
        reqs.append({"m": r.method, "u": u, "t": r.resource_type})
    page.on("request", on_req)
    page.goto("https://www.dota2.com/crownfall", timeout=60000, wait_until="domcontentloaded")
    time.sleep(12)
    browser.close()

seen = set()
for r in reqs:
    k = r["m"] + " " + r["u"]
    if k not in seen:
        seen.add(k)
        print(f'{r["m"]:6s} {r["t"]:10s} {r["u"][:170]}')
print(f"\n共 {len(seen)} 个")
