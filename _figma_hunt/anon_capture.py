"""匿名打开公开 Figma 文件，捕获全部 XHR 请求（API 清单的确定性来源）
"""
import sys, json, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KEY = "bv2nMIdFf4u3dESGail4sm"
reqs = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()

    def on_request(req):
        if req.resource_type in ("xhr", "fetch"):
            body = ""
            try:
                if req.method in ("POST", "PUT", "PATCH"):
                    body = req.post_data or ""
            except Exception:
                pass
            reqs.append({"method": req.method, "url": req.url, "body": body[:500]})

    page.on("request", on_request)
    page.goto(f"https://www.figma.com/file/{KEY}", wait_until="domcontentloaded", timeout=60000)
    time.sleep(15)  # 等初始加载

    json.dump(reqs, open(r"D:\scan\_figma_hunt\anon_xhr.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("捕获 XHR 数:", len(reqs))
    for r_ in reqs:
        print(r_["method"], r_["url"][:140])
    browser.close()
