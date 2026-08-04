# -*- coding: utf-8 -*-
"""Playwright 捕获 dota2.com SPA 真实 API 请求(直连,不走系统代理)"""
import time
from playwright.sync_api import sync_playwright

reqs = []

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="msedge",
        headless=True,
        args=["--no-proxy-server"],
    )
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )

    def on_req(r):
        u = r.url
        if any(k in u for k in (".js", ".css", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".woff", ".ico", ".gif", ".mp4", ".webm")):
            return
        reqs.append({"method": r.method, "url": u, "type": r.resource_type})

    page.on("request", on_req)
    page.goto("https://www.dota2.com/", timeout=90000, wait_until="domcontentloaded")
    time.sleep(15)  # 等 SPA 渲染 + 客户端 API 请求
    page.goto("https://www.dota2.com/newsentry/2870472829293831072", timeout=90000, wait_until="domcontentloaded")
    time.sleep(10)
    browser.close()

seen = set()
for r in reqs:
    k = r["method"] + " " + r["url"]
    if k not in seen:
        seen.add(k)
        print(f'{r["method"]:6s} {r["type"]:10s} {r["url"][:160]}')
print(f"\n共 {len(seen)} 个请求")
