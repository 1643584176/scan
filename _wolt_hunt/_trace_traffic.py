# -*- coding: utf-8 -*-
"""用无头浏览器跑 wolt.com 页面，拦截真实 API 请求，还原业务流程"""
import json, sys, time
from playwright.sync_api import sync_playwright

REQUESTS = []

def hook(route):
    req = route.request
    if req.resource_type in ("xhr", "fetch", "document"):
        REQUESTS.append({
            "method": req.method,
            "url": req.url,
            "headers": dict(req.headers),
        })
    route.continue_()

def dump(tag):
    print(f"\n########## {tag} ##########")
    seen = set()
    for r in REQUESTS:
        key = (r["method"], r["url"].split("?")[0])
        if key in seen:
            continue
        seen.add(key)
        h = r["headers"]
        auth = h.get("authorization", "")
        if len(auth) > 40:
            auth = auth[:40] + "..."
        print(f"  {r['method']:6s} {r['url'][:150]}")
        print(f"        auth={auth} cookies={h.get('cookie','')[:80]}")
    return len(seen)

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="msedge", headless=True,
        args=["--no-proxy-server", "--disable-blink-features=AutomationControlled"],
    )
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        locale="en-US",
        extra_http_headers={"X-HackerOne-Research": "pccp"},
    )
    page = ctx.new_page()
    page.route("**/*", hook)

    # 1. 首页
    page.goto("https://wolt.com/en", timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    dump("HOME")
    REQUESTS.clear()

    # 2. 测试 venue 页
    page.goto("https://wolt.com/en/fin/helsinki/venue/test-670e7897e3c56dcc5b5a0989-sh0p",
              timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    dump("VENUE")
    REQUESTS.clear()

    # 3. 拼单加入页（游客入口）
    page.goto("https://wolt.com/en/group-order/join", timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    dump("GROUP-ORDER-JOIN")

    # 4. localStorage 与 cookies（游客令牌可能存这里）
    print("\n########## STORAGE ##########")
    for k, v in ctx.storage_state()["cookies"]:
        if "wolt" in k["domain"]:
            print(f"  cookie {k['name']} = {k['value'][:60]}")
    ls = page.evaluate("JSON.stringify(Object.keys(localStorage))")
    print(f"  localStorage keys: {ls}")
    for key in ["wolt-token", "wolt.access_token", "access_token", "authToken"]:
        val = page.evaluate(f"localStorage.getItem('{key}')")
        if val:
            print(f"  localStorage[{key}] = {str(val)[:100]}")

    browser.close()
