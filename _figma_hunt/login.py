"""Figma 自动登录（Playwright）：处理 AWS WAF challenge 后登录并提取 session
凭据来源：用户提供的 Figma 测试账号（仅本项目使用，不入记忆）
"""
import sys, time, json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 新测试账号（2026-08-07 起启用）；旧账号 1643584176@qq.com 同密码
EMAIL = "729488839@qq.com"
PWD = "Agent360User$5h2!QxR"
OUT = r"D:\scan\_figma_hunt\figma_session.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context()
    page = ctx.new_page()

    print("打开登录页...")
    page.goto("https://www.figma.com/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)  # 等 WAF challenge 自动完成

    page.screenshot(path=r"D:\scan\_figma_hunt\login_1.png")
    print("已截图 login_1.png，页面标题:", page.title())

    # 尝试定位 email 输入框（多种可能）
    email_input = None
    for sel in ['input[type="email"]', 'input[name="email"]', 'input[placeholder*="mail"]']:
        loc = page.locator(sel).first
        if loc.count() > 0:
            email_input = loc
            print("email 输入框:", sel)
            break
    if not email_input:
        print("未找到 email 输入框，打印页面文本:")
        print(page.inner_text("body")[:500])
        input("按回车继续...")
        email_input = page.locator('input').first

    email_input.fill(EMAIL)
    page.wait_for_timeout(1000)
    page.screenshot(path=r"D:\scan\_figma_hunt\login_2.png")

    # 点提交按钮（多种候选文本）
    clicked = False
    for txt in ["Continue", "Log in", "Login", "Next", "继续"]:
        btn = page.get_by_role("button", name=txt)
        if btn.count() > 0:
            btn.first.click()
            print("点击按钮:", txt)
            clicked = True
            break
    if not clicked:
        page.keyboard.press("Enter")
        print("未匹配到按钮，用 Enter 提交")

    page.wait_for_timeout(5000)
    page.screenshot(path=r"D:\scan\_figma_hunt\login_3.png")

    # 找密码框
    pwd_input = page.locator('input[type="password"]').first
    if pwd_input.count() > 0:
        pwd_input.fill(PWD)
        page.wait_for_timeout(500)
        for txt in ["Log in", "Login", "Continue", "Sign in", "登录"]:
            btn = page.get_by_role("button", name=txt)
            if btn.count() > 0:
                btn.first.click()
                print("点击登录:", txt)
                break
        else:
            page.keyboard.press("Enter")
    else:
        print("未出现密码框（可能已进入或需其他步骤）")

    # 等待登录完成（URL 变化或 cookie 出现）
    for i in range(30):
        time.sleep(2)
        cookies = ctx.cookies()
        names = [c["name"] for c in cookies]
        if page.url and "login" not in page.url and any(n in names for n in ["figma.session", "session", "token"]):
            break
    page.wait_for_timeout(3000)
    page.screenshot(path=r"D:\scan\_figma_hunt\login_4.png")

    cookies = ctx.cookies()
    json.dump(cookies, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("URL:", page.url)
    print(f"cookies 已存 {OUT} ({len(cookies)} 个):")
    for c in cookies:
        print("  ", c["name"], "=", c["value"][:40], "..." if len(c["value"]) > 40 else "")

    input("按回车关闭浏览器...")
    browser.close()
