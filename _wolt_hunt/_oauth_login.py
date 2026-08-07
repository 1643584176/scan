# -*- coding: utf-8 -*-
"""1secmail 邮箱走 corporate OAuth 登录，抓 access_token
流程: authorize -> login(填email) -> /login/email/sent -> 轮询1secmail -> magic link/验证码 -> 完成授权 -> 换token
"""
import sys, json, time, requests, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

# ===== 1. 1secmail 注册 =====
def secmail_new():
    r = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1", timeout=15)
    addr = r.json()[0]
    login, domain = addr.split("@")
    return addr, login, domain

def secmail_check(login, domain):
    try:
        r = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}", timeout=12)
        return r.json() or []
    except Exception:
        return []

def secmail_read(login, domain, mid):
    r = requests.get(f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={mid}", timeout=12)
    return r.json()

addr, login, domain = secmail_new()
print(f"[1] 1secmail: {addr}")

CAP = {"token": None, "calls": []}

def on_response(resp):
    if "authentication" in resp.url:
        try:
            t = resp.text()[:400]
            if t.startswith("{"):
                print(f"  [RESP] {resp.status} {resp.url[:110]} -> {t[:180]}")
                m = re.search(r'"access_token"\s*:\s*"([^"]+)"', t)
                if m:
                    CAP["token"] = m.group(1)
        except Exception:
            pass

def on_request(req):
    if req.resource_type in ("xhr", "fetch"):
        try:
            body = (req.post_data_buffer.tobytes().decode("utf-8", errors="replace") if req.post_data_buffer else "")[:200]
        except Exception:
            body = ""
        if "authentication" in req.url or "oauth" in req.url:
            print(f"  [REQ] {req.method} {req.url[:130]}")
            if body:
                print(f"        {body[:180]}")

with sync_playwright() as p:
    br = p.chromium.launch(channel="msedge", headless=True, args=["--no-proxy-server"])
    ctx = br.new_context(viewport={"width": 1440, "height": 900}, locale="en-US")
    page = ctx.new_page()
    page.on("response", on_response)
    page.on("request", on_request)

    print("[2] OAuth authorize -> login page")
    url = ("https://authentication.wolt.com/oauth2/authorize?client_id=woltatwork-admin"
           "&redirect_uri=https%3A%2F%2Fcorporate.wolt.com%2Foauth2%2Flogin-callback"
           "&response_type=code&code_challenge=abc123&code_challenge_method=S256")
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    page.locator('input[name="email"]').fill(addr, timeout=5000)
    page.wait_for_timeout(800)
    page.locator('button[type="submit"]').first.click(timeout=5000, no_wait_after=True)
    print("[3] Submitted email, waiting for redirect...")
    page.wait_for_timeout(4000)
    print(f"  URL: {page.url[:130]}")

    # ===== 4. 轮询 1secmail =====
    print("[4] Polling 1secmail...")
    magic = None
    for attempt in range(20):
        time.sleep(4)
        msgs = secmail_check(login, domain)
        if msgs:
            mid = msgs[0]["id"]
            full = secmail_read(login, domain, mid)
            html = (full.get("html") or "") + (full.get("text") or "")
            print(f"  mail: {msgs[0].get('subject','')[:60]}")
            # 提取链接
            links = re.findall(r"https?://[^\s\"'<>]+", html)
            for l in links:
                if "wolt" in l.lower() and "callback" in l.lower() or "login" in l.lower():
                    magic = l.replace("&amp;", "&")
                    print(f"  !! MAGIC: {magic[:160]}")
                    break
            if not magic:
                codes = re.findall(r"\b(\d{4,8})\b", html)
                if codes:
                    magic = codes[0]
                    print(f"  !! CODE: {magic}")
            if magic:
                break
        if attempt % 5 == 4:
            print(f"  ...{attempt+1}0s no mail")

    # ===== 5. 使用 magic link / 输入验证码 =====
    if magic:
        if magic.startswith("http"):
            print("[5] Opening magic link...")
            page.goto(magic, timeout=45000, wait_until="domcontentloaded")
        else:
            print("[5] Entering code...")
            # 找验证码输入框
            inputs = page.locator("input").all()
            for i, ch in enumerate(magic[:6]):
                if i < len(inputs):
                    try: inputs[i].fill(ch, timeout=3000)
                    except Exception: pass
            try:
                page.locator('button[type="submit"]').first.click(timeout=4000, no_wait_after=True)
            except Exception:
                pass
        for i in range(10):
            page.wait_for_timeout(2500)
            print(f"  ... t={i*2.5}s URL: {page.url[:130]}")
            if CAP["token"] or "callback" in page.url or "code=" in page.url:
                break
        print(f"  final URL: {page.url[:160]}")
    else:
        print("[5] NO MAGIC LINK/CODE")

    br.close()

if CAP["token"]:
    json.dump({"access_token": CAP["token"]}, open(r"D:\scan\_wolt_hunt\_wolt_token.json", "w", encoding="utf-8"), indent=2)
    print(f"\n[OK] TOKEN: {CAP['token'][:60]}...")
else:
    print("\n[FAIL] no token")
