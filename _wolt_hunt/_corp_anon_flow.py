# -*- coding: utf-8 -*-
"""corporate.wolt.com 未登录流量抓取：理解企业端启动加载的真实 API"""
import sys, json, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

REQS = []

def on_request(req):
    if req.resource_type in ("xhr", "fetch"):
        try:
            body = (req.post_data_buffer.tobytes().decode("utf-8", errors="replace") if req.post_data_buffer else "")[:300]
        except:
            body = ""
        REQS.append({"m": req.method, "u": req.url, "body": body})
        print(f"[REQ] {req.method} {req.url[:170]}")
        if body:
            print(f"      {body[:240]}")

def on_response(resp):
    if any(k in resp.url for k in ("gatekeeper", "corporate", "auth", "api")):
        try:
            txt = resp.text()[:400]
            print(f"[RESP] {resp.status} {resp.url[:150]}")
            print(f"       {txt[:350]}")
        except:
            pass

with sync_playwright() as p:
    br = p.chromium.launch(channel="msedge", headless=True, args=["--no-proxy-server"])
    ctx = br.new_context(viewport={"width": 1440, "height": 900}, locale="en-US")
    page = ctx.new_page()
    page.on("request", on_request)
    page.on("response", on_response)
    print("[1] Opening corporate.wolt.com...")
    page.goto("https://corporate.wolt.com", timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    print(f"  URL: {page.url[:120]}")
    print(f"  Title: {page.title()[:80]}")
    try:
        page.screenshot(path="D:/scan/_wolt_hunt/_payment_shots/corp_anon.png")
    except:
        pass
    br.close()

json.dump(REQS, open(r"D:\scan\_wolt_hunt\_corp_anon_flow.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"\n[DONE] {len(REQS)} API calls")
