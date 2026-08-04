# -*- coding: utf-8 -*-
"""打开 venue 页并点击加购，抓 unified-gateway.dashapi.com 请求的完整 headers/body/响应
   目标：确认 Pedregal 网关的认证机制（header? cookie? token 来源）"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

captured = []

def hook(route):
    req = route.request
    if "unified-gateway" in req.url or "dashapi" in req.url:
        captured.append({
            "m": req.method, "u": req.url,
            "h": dict(req.headers),
            "post": req.post_data[:2500] if req.post_data else None,
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

    # venue 页（有可加购商品）
    page.goto("https://wolt.com/en/fin/helsinki/venue/test-670e7897e3c56dcc5b5a0989-sh0p",
              timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    print(f"########## 页面加载后 unified-gateway/dashapi 请求 ({len(captured)}) ##########")
    for r in captured:
        print(f"  {r['m']:5s} {r['u'][:150]}")
        interesting = {k: v for k, v in r["h"].items() if k not in ("user-agent", "accept", "accept-language", "accept-encoding", "sec-fetch-*", "sec-ch-ua*")}
        print(f"        headers: {json.dumps(interesting, ensure_ascii=False)[:600]}")
        if r["post"]:
            print(f"        body: {r['post'][:600]}")
    captured.clear()

    # 尝试加购
    try:
        add_btns = page.locator("button:has-text('Add'), [data-test-id*='add'], [data-test-id*='Add']")
        n = add_btns.count()
        print(f"\n  add-buttons: {n}")
        if n > 0:
            add_btns.first.click(timeout=8000)
            page.wait_for_timeout(6000)
            print(f"\n########## 点击 Add 后 unified-gateway/dashapi 请求 ({len(captured)}) ##########")
            for r in captured:
                print(f"  {r['m']:5s} {r['u'][:150]}")
                interesting = {k: v for k, v in r["h"].items() if k not in ("user-agent", "accept", "accept-language", "accept-encoding", "sec-fetch-*", "sec-ch-ua*")}
                print(f"        headers: {json.dumps(interesting, ensure_ascii=False)[:800]}")
                if r["post"]:
                    print(f"        body: {r['post'][:800]}")
    except Exception as e:
        print(f"  add-click err: {e}")

    # 打印所有 cookie 域，看有没有 guest/token cookie
    cookies = ctx.cookies()
    print("\n########## cookies ##########")
    for c in cookies:
        if any(k in c["name"].lower() for k in ("token", "auth", "guest", "session", "sid", "jwt", "dd_")):
            print(f"  {c['domain']} {c['name']} = {c['value'][:60]}")

    b.close()
