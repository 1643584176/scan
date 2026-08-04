# -*- coding: utf-8 -*-
"""打开 venue 页，抓 dashapi/cx 请求的完整 headers+body，并尝试加购物车触发 cx API"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

captured = []

def hook(route):
    req = route.request
    if "dashapi.com" in req.url or "cx/v1" in req.url or "carts" in req.url:
        captured.append({
            "m": req.method, "u": req.url,
            "h": dict(req.headers),
            "post": req.post_data[:2000] if req.post_data else None,
        })
    route.continue_()

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True, args=["--no-proxy-server"])
    ctx = b.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        locale="en-US",
        extra_http_headers={"X-HackerOne-Research": "pccp"},
    )
    page = ctx.new_page()
    page.route("**/*", hook)

    # venue 页（加载时可能预取购物车/评估）
    page.goto("https://wolt.com/en/fin/helsinki/venue/test-670e7897e3c56dcc5b5a0989-sh0p",
              timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    print(f"\n########## VENUE 页 dashapi/cx 请求 ({len(captured)}) ##########")
    for r in captured:
        print(f"  {r['m']:5s} {r['u'][:160]}")
        h = r["h"]
        interesting = {k: v for k, v in h.items() if k not in ("user-agent", "accept", "accept-language", "accept-encoding", "sec-fetch-*", "sec-ch-ua*")}
        print(f"        headers: {json.dumps(interesting, ensure_ascii=False)[:400]}")
        if r["post"]:
            print(f"        body: {r['post'][:300]}")
    captured.clear()

    # 尝试加购物车：找 Add 按钮点击（游客也可加）
    try:
        add_btns = page.locator("button:has-text('Add'), [data-test-id*='add'], [data-test-id*='Add']")
        n = add_btns.count()
        print(f"\n  add-buttons found: {n}")
        if n > 0:
            add_btns.first.click(timeout=8000)
            page.wait_for_timeout(6000)
            print(f"\n########## 点击 Add 后 dashapi/cx 请求 ({len(captured)}) ##########")
            for r in captured:
                print(f"  {r['m']:5s} {r['u'][:160]}")
                h = r["h"]
                interesting = {k: v for k, v in h.items() if k not in ("user-agent", "accept", "accept-language", "accept-encoding", "sec-fetch-*", "sec-ch-ua*")}
                print(f"        headers: {json.dumps(interesting, ensure_ascii=False)[:400]}")
                if r["post"]:
                    print(f"        body: {r['post'][:300]}")
    except Exception as e:
        print(f"  add-click err: {e}")

    # 打印页面上的商品卡片（看测试 venue 有没有可加购的商品）
    try:
        items = page.locator("[data-test-id*='item'], [class*='ItemCard'], article").count()
        print(f"  item cards: {items}")
        # 截图看页面状态
        page.screenshot(path="D:/scan/_wolt_hunt/_venue_add.png")
    except Exception as e:
        print(f"  inspect err: {e}")

    b.close()
