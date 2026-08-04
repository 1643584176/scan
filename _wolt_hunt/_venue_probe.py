# -*- coding: utf-8 -*-
"""抓真实 venue 页完整 API 面 + SSR 数据中的敏感字段"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

REQS = []

def hook(route):
    req = route.request
    if req.resource_type in ("xhr", "fetch"):
        REQS.append({"m": req.method, "u": req.url, "h": dict(req.headers)})
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

    # 真实 venue：赫尔辛基一家真实餐厅（从首页热门找）
    page.goto("https://wolt.com/en/fin/helsinki", timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    # 提取首页 venue 链接
    links = page.evaluate("""() => Array.from(document.querySelectorAll('a[href*="/venue/"]'))
        .map(a => a.getAttribute('href')).filter(h => h && !h.includes('test-')).slice(0, 10)""")
    print("VENUE LINKS:", json.dumps(links, ensure_ascii=False)[:500])
    target = links[0] if links else None

    if target:
        REQS.clear()
        page.goto("https://wolt.com" + target, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(8000)
        print(f"\n########## REAL VENUE API ({target}) ##########")
        seen = set()
        for r in REQS:
            key = (r["m"], r["u"].split("?")[0])
            if key in seen:
                continue
            seen.add(key)
            h = r["h"]
            auth = "AUTH" if h.get("authorization") else "no-auth"
            print(f"  {r['m']:5s} {auth:8s} {r['u'][:170]}")
        # SSR 数据里找隐藏字段（script#__NEXT_DATA__ 或 wolt 特有）
        try:
            html = page.content()
            print(f"\n  page size: {len(html)}")
            # 找嵌入 JSON 中的 email/phone/internal 字段
            import re
            for pat in ["support_email", "internal_id", "is_test", "test_venue", "internal"]:
                ms = re.findall(pat + r'[^,}]{0,60}', html)
                if ms:
                    print(f"  SSR[{pat}]: {ms[:3]}")
        except Exception as e:
            print(f"  ssr err: {e}")

    b.close()
