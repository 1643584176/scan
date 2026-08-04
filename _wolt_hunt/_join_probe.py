# -*- coding: utf-8 -*-
"""访问 group-order/{code}/join 页面，抓取真实 join API 请求"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

captured = []

def hook(route):
    req = route.request
    if req.resource_type in ("xhr", "fetch"):
        captured.append({"m": req.method, "u": req.url, "h": dict(req.headers)})
    route.continue_()

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True, args=["--no-proxy-server"])
    ctx = b.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        extra_http_headers={"X-HackerOne-Research": "pccp"},
    )
    page = ctx.new_page()
    page.route("**/*", hook)

    # 带 code 的 join URL（模仿邀请链接）
    for code in ["123456", "test"]:
        captured.clear()
        try:
            page.goto(f"https://wolt.com/en/group-order/{code}/join",
                      timeout=45000, wait_until="domcontentloaded")
            page.wait_for_timeout(6000)
        except Exception as e:
            print(f"[{code}] goto err: {e}")
        print(f"\n########## URL /en/group-order/{code}/join ##########")
        for r in captured:
            print(f"  {r['m']:5s} {r['u'][:160]}")
            if "group_order" in r["u"] or "guest" in r["u"]:
                print(f"        headers: auth={r['h'].get('authorization','')[:50]}")
        # 页面标题/内容
        try:
            title = page.title()
            print(f"  PAGE: {title}")
        except Exception:
            pass

    b.close()
