"""登录旧账号 1643584176@qq.com（非协作者对照账号），无头模式，非交互

用途：file_proxy/design_systems 等接口的非协作者视角测试。
旧账号密码与新账号相同（login.py 注释确认）。
"""
import sys, time, json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EMAIL = "1643584176@qq.com"
PWD = "Agent360User$5h2!QxR"
OUT = r"D:\scan\_figma_hunt\figma_session_alt.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()

    print("打开登录页...")
    page.goto("https://www.figma.com/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(9000)  # 等 WAF challenge

    # 输入 email
    filled = False
    for sel in ['input[type="email"]', 'input[name="email"]', 'input[placeholder*="mail"]']:
        loc = page.locator(sel).first
        if loc.count() > 0:
            loc.fill(EMAIL)
            print("email 输入:", sel)
            filled = True
            break
    if not filled:
        print("无 email 框，页面文本:", page.inner_text("body")[:300])
        browser.close()
        sys.exit(1)

    page.wait_for_timeout(800)
    clicked = False
    for txt in ["Continue", "Log in", "Login", "Next"]:
        btn = page.get_by_role("button", name=txt)
        if btn.count() > 0:
            btn.first.click()
            print("点击:", txt)
            clicked = True
            break
    if not clicked:
        page.keyboard.press("Enter")

    page.wait_for_timeout(5000)

    pwd = page.locator('input[type="password"]').first
    if pwd.count() > 0:
        pwd.fill(PWD)
        page.wait_for_timeout(500)
        for txt in ["Log in", "Login", "Continue", "Sign in"]:
            btn = page.get_by_role("button", name=txt)
            if btn.count() > 0:
                btn.first.click()
                print("点击登录:", txt)
                break
        else:
            page.keyboard.press("Enter")
    else:
        print("无密码框，当前 URL:", page.url)

    # 等待登录完成
    for i in range(30):
        time.sleep(2)
        cookies = ctx.cookies()
        names = [c["name"] for c in cookies]
        if page.url and "login" not in page.url and "figma.session" in names:
            break

    cookies = ctx.cookies()
    json.dump(cookies, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("URL:", page.url)
    print(f"cookies 已存 {OUT} ({len(cookies)} 个)")
    for c in cookies:
        if c["name"] in ("figma.session", "figma.mst", "__Host-figma.authn"):
            print("  ", c["name"], "=", c["value"][:50])
    browser.close()
