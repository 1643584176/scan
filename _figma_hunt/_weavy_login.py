"""Weave 登录自动化:Playwright 打开 app.weavy.ai,用户手动完成 Figma OAuth 授权
脚本自动拦截 api.weavy.ai 请求,提取 Authorization Bearer token 保存
用法:运行后弹窗浏览器,用户登录 Figma(B账号)并授权 Weave
"""
import sys, time, json, io
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOKEN_FILE = "weavy_token.txt"
CAPTURED = {"token": None, "url": None, "headers": None}

def on_request(request):
    if "api.weavy.ai" in request.url and "token" in (request.headers.get("authorization", "").lower()):
        if CAPTURED["token"] is None:
            CAPTURED["token"] = request.headers.get("authorization")
            CAPTURED["url"] = request.url
            CAPTURED["headers"] = dict(request.headers)
            print(f"✅ 抓到 Bearer token: {CAPTURED['token'][:80]}...")
            print(f"   URL: {request.url[:120]}")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.on("request", on_request)
    page.goto("https://app.weavy.ai", timeout=60000)
    print("=== 浏览器已打开 app.weavy.ai ===")
    print("请在弹出的窗口中: 1) 点 Sign In  2) 用 B 账号(729488839@qq.com)登录 Figma(如未登录)")
    print("3) 授权 Weave 应用。脚本会自动捕获 token,无需其他操作。")
    deadline = time.time() + 600
    while time.time() < deadline:
        if CAPTURED["token"]:
            break
        time.sleep(2)
    if CAPTURED["token"]:
        io.open(TOKEN_FILE, "w", encoding="utf-8").write(CAPTURED["token"])
        print(f"\n=== 已保存 {TOKEN_FILE} ===")
    else:
        print("\n❌ 超时未捕获 token")
    input("按回车关闭浏览器...")
    browser.close()
