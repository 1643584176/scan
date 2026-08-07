"""用新邮箱 729488839@qq.com 重新登录（headless），验证是否与旧邮箱同账户"""
import sys, time, json, base64, re
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EMAIL = "729488839@qq.com"
PWD = "Agent360User$5h2!QxR"
OUT = r"D:\scan\_figma_hunt\figma_session_new.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()

    page.goto("https://www.figma.com/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(9000)

    for sel in ['input[type="email"]', 'input[name="email"]', 'input[placeholder*="mail"]']:
        loc = page.locator(sel).first
        if loc.count() > 0:
            loc.fill(EMAIL)
            print("email 输入:", sel)
            break

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
        print("无密码框，URL:", page.url)

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
    d = {c["name"]: c["value"] for c in cookies}
    s = d.get("figma.session", "")
    try:
        raw = base64.b64decode(s + "=" * (-len(s) % 4))
        text = raw.decode("latin-1")
        m = re.search(r"username.{0,60}", text)
        print(">>> session 内部 username:", m.group(0) if m else "无")
    except Exception as e:
        print("解码失败:", e)
    a = d.get("__Host-figma.authn", "")
    print(">>> authn:", a[:90])
    browser.close()
