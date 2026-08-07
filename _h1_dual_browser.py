"""H1 双无痕浏览器：两个独立 session 登录两个 H1 账户
用法：运行后两个 Chromium 窗口打开 H1 登录页，用户手动登录（过人机验证）
登录完成后脚本自动提取两个 context 的 cookies 存文件，供后续 API 测试用
"""
import sys, time, json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT_A = r"D:\scan\_h1_session_a.json"
OUT_B = r"D:\scan\_h1_session_b.json"

def wait_login(page, ctx, name, timeout_s=300):
    """等待用户登录完成：检测到 session cookie 即认为登录成功"""
    print(f"[{name}] 请在该窗口登录 H1 账户（处理人机验证）...")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        cookies = ctx.cookies()
        if any("session" in c["name"].lower() for c in cookies):
            print(f"[{name}] 登录成功: session cookie 已出现")
            return cookies
        time.sleep(2)
    print(f"[{name}] 等待超时")
    return None

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx_a = browser.new_context()
    ctx_b = browser.new_context()
    page_a = ctx_a.new_page()
    page_b = ctx_b.new_page()

    page_a.goto("https://hackerone.com/login", wait_until="domcontentloaded")
    page_b.goto("https://hackerone.com/login", wait_until="domcontentloaded")
    print("=== 两个无痕窗口已打开 H1 登录页 ===")
    print("窗口 A（左）登录账户 A，窗口 B（右）登录账户 B")
    print("登录时如遇人机验证请手动完成")

    ca = wait_login(page_a, ctx_a, "窗口A")
    cb = wait_login(page_b, ctx_b, "窗口B")

    if ca:
        json.dump(ca, open(OUT_A, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"窗口A cookies -> {OUT_A} ({len(ca)} 个)")
    if cb:
        json.dump(cb, open(OUT_B, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"窗口B cookies -> {OUT_B} ({len(cb)} 个)")

    print("=== 提取完成。浏览器保持打开，可继续人工操作 ===")
    input("按回车关闭浏览器...")
    browser.close()
