# -*- coding: utf-8 -*-
"""Wolt 消费者登录拿 JWT：playwright 走邮箱验证码，拦截 auth API 响应抓 access_token
1) 复用/注册 mail.tm 临时邮箱  2) wolt.com log in 流程  3) 保存 token 到 _wolt_token.json
"""
import sys, json, os, time, requests, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

SHOT = "D:/scan/_wolt_hunt/_payment_shots"
os.makedirs(SHOT, exist_ok=True)
MAIL_PASS = "PccpTest123!"

creds = json.load(open(r"D:\scan\_wolt_hunt\_wolt_creds.json", encoding="utf-8"))
email, mail_token = creds["email"], creds["mail_token"]
MAIL_HEADERS = {"Authorization": f"Bearer {mail_token}"}

# ===== 0. 验证 mail.tm 邮箱可用性 =====
try:
    r = requests.get("https://api.mail.tm/messages", headers=MAIL_HEADERS, timeout=10)
    if r.status_code == 200:
        print(f"[0] mail.tm OK, existing msgs: {len(r.json().get('hydra:member', []))}")
    else:
        raise Exception(f"mail.tm {r.status_code}")
except Exception as e:
    print(f"[0] mail.tm 过期({e})，注册新邮箱")
    dr = requests.get("https://api.mail.tm/domains", timeout=10)
    domain = dr.json()["hydra:member"][0]["domain"]
    ts = str(int(time.time()))[-8:]
    email = f"pccp{ts}@{domain}"
    r = requests.post("https://api.mail.tm/accounts", json={"address": email, "password": MAIL_PASS}, timeout=15)
    r2 = requests.post("https://api.mail.tm/token", json={"address": email, "password": MAIL_PASS}, timeout=15)
    mail_token = r2.json()["token"]
    MAIL_HEADERS = {"Authorization": f"Bearer {mail_token}"}
    json.dump({"email": email, "password": MAIL_PASS, "mail_token": mail_token},
              open(r"D:\scan\_wolt_hunt\_wolt_creds.json", "w", encoding="utf-8"), indent=2)
    print(f"    新邮箱: {email}")

# ===== 1. 浏览器登录，抓 token =====
CAPTURED = {"token": None, "api_calls": []}

def on_response(resp):
    """监听响应，抓 auth API 里的 access_token（不阻断请求）"""
    url = resp.url
    if any(k in url for k in ("wauth2", "token", "oauth2", "auth")):
        try:
            txt = resp.text()[:2000]
            if "access_token" in txt or "email_login" in url or "verification" in url:
                print(f"  [RESP] {url[:120]} -> {txt[:300]}")
            m = re.search(r'"access_token"\s*:\s*"([^"]+)"', txt)
            if m and not CAPTURED["token"]:
                CAPTURED["token"] = m.group(1)
                print(f"  !! CAPTURED access_token: {m.group(1)[:50]}...")
        except Exception:
            pass

def on_request(req):
    if req.resource_type in ("xhr", "fetch"):
        try:
            body = (req.post_data_buffer.tobytes().decode("utf-8", errors="replace") if req.post_data_buffer else "")[:400]
        except:
            body = ""
        CAPTURED["api_calls"].append({"m": req.method, "u": req.url, "body": body})
        if any(k in req.url for k in ("auth", "login", "token", "wauth2")):
            print(f"  [REQ] {req.method} {req.url[:160]}")
            if body:
                print(f"        {body[:220]}")

with sync_playwright() as p:
    br = p.chromium.launch(channel="msedge", headless=True, args=["--no-proxy-server"])
    ctx = br.new_context(viewport={"width": 1440, "height": 900}, locale="en-US")
    page = ctx.new_page()
    page.on("response", on_response)
    page.on("request", on_request)

    print("[1] Opening wolt.com...")
    page.goto("https://wolt.com/en/fin", timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    try: page.locator('[data-test-id="decline-button"]').click(timeout=3000)
    except: pass
    page.wait_for_timeout(1000)

    print("[2] Clicking Log in...")
    page.locator('[data-test-id="UserStatus.Login"]').click(timeout=8000)
    page.wait_for_timeout(3000)

    print("[3] Filling email...")
    page.locator('input[type="email"]').first.fill(email, timeout=5000)
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{SHOT}/login2_1.png")

    # 检查是否有 "via email" 选项
    try:
        page.locator('[data-test-id="MethodSelect.Email"]').click(timeout=2000)
        print("  -> 选择 email 验证方式")
    except:
        pass

    print("[4] Clicking Continue...")
    try:
        page.locator('[data-test-id="StepMethodSelect.NextButton"]').click(timeout=5000, no_wait_after=True)
    except Exception as e:
        print(f"  NextButton 失败: {e}")

    # ===== 轮询邮箱验证码 =====
    print("[5] Polling mail.tm for code...")
    code = None
    for attempt in range(20):
        time.sleep(4)
        try:
            r = requests.get("https://api.mail.tm/messages", headers=MAIL_HEADERS, timeout=10)
            msgs = r.json().get("hydra:member", [])
            if msgs:
                mid = msgs[0]["id"]
                r2 = requests.get(f"https://api.mail.tm/messages/{mid}", headers=MAIL_HEADERS, timeout=10)
                full = r2.json()
                html = (full.get("html") or "") + (full.get("text") or "")
                print(f"  mail: {full.get('subject','')[:60]}")
                codes = re.findall(r"\b(\d{4,8})\b", html)
                if codes:
                    code = codes[0]
                    print(f"  !! CODE: {code}")
                    break
        except Exception as e:
            print(f"  poll err: {str(e)[:60]}")

    if code:
        print("[6] Entering code...")
        for i, digit in enumerate(code[:6]):
            sel = f'input[data-test-id="CodeVerification.DigitInput"]'
            try:
                page.locator(sel).nth(i).fill(digit, timeout=3000)
            except:
                try:
                    page.locator(f'input:not([type="email"])').nth(i).fill(digit, timeout=3000)
                except: pass
        page.wait_for_timeout(4000)
        page.screenshot(path=f"{SHOT}/login2_2_code.png")

    # ===== 等待 token 出现 =====
    print("[7] Waiting for token...")
    for _ in range(12):
        page.wait_for_timeout(2500)
        if CAPTURED["token"]:
            break
    page.screenshot(path=f"{SHOT}/login2_final.png")
    print(f"  final URL: {page.url[:120]}")

    # 尝试从 localStorage 读
    if not CAPTURED["token"]:
        for src in ["localStorage", "sessionStorage"]:
            try:
                items = page.evaluate(f"() => Object.entries({src})")
                for k, v in items:
                    if any(t in k.lower() for t in ("token", "auth", "session", "jwt")):
                        print(f"  {src}[{k}] = {str(v)[:120]}")
                        m = re.search(r'"access_token"\s*:\s*"([^"]+)"', str(v))
                        if m: CAPTURED["token"] = m.group(1)
            except Exception as e:
                print(f"  {src}: {str(e)[:60]}")
    br.close()

if CAPTURED["token"]:
    json.dump({"access_token": CAPTURED["token"]}, open(r"D:\scan\_wolt_hunt\_wolt_token.json", "w", encoding="utf-8"), indent=2)
    print(f"\n[OK] token saved: {CAPTURED['token'][:60]}...")
else:
    print("\n[FAIL] no token captured. API calls:")
    for c in CAPTURED["api_calls"][-15:]:
        print(f"  {c['m']} {c['u'][:140]}")
