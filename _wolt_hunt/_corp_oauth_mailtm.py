"""corporate OAuth 完整登录：mail.tm 邮箱收 magic link -> 完成授权 -> 换 corporate token
流程: authorize -> 填email -> /login/email/sent -> 轮询 mail.tm -> magic link -> 回调 -> 换 token
"""
import sys, json, time, requests, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

SHOT = "D:/scan/_wolt_hunt/_payment_shots"
creds = json.load(open(r"D:\scan\_wolt_hunt\_wolt_creds.json", encoding="utf-8"))
email, mail_token = creds["email"], creds["mail_token"]
MAIL_H = {"Authorization": f"Bearer {mail_token}"}

CAP = {"token": None, "calls": []}

def on_response(resp):
    url, st = resp.url, resp.status
    if any(k in url for k in ("authentication", "oauth", "token", "callback", "wauth2")):
        try:
            t = resp.text()[:500]
        except Exception:
            t = ""
        print(f"  [RESP] {st} {url[:130]}")
        if t.startswith("{"):
            print(f"        {t[:300]}")
        m = re.search(r'"access_token"\s*:\s*"([^"]+)"', t)
        if m and not CAP["token"]:
            CAP["token"] = m.group(1)
            print(f"  !! TOKEN: {m.group(1)[:60]}")

def on_request(req):
    if req.resource_type in ("xhr", "fetch"):
        try:
            body = (req.post_data_buffer.tobytes().decode("utf-8", errors="replace") if req.post_data_buffer else "")[:200]
        except Exception:
            body = ""
        if any(k in req.url for k in ("authentication", "oauth", "token", "wauth2")):
            print(f"  [REQ] {req.method} {req.url[:130]}")
            if body:
                print(f"        {body[:180]}")

with sync_playwright() as p:
    br = p.chromium.launch(channel="msedge", headless=True, args=["--no-proxy-server"])
    ctx = br.new_context(viewport={"width": 1440, "height": 900}, locale="en-US")
    page = ctx.new_page()
    page.on("response", on_response)
    page.on("request", on_request)

    print("[1] OAuth authorize")
    url = ("https://authentication.wolt.com/oauth2/authorize?client_id=woltatwork-admin"
           "&redirect_uri=https%3A%2F%2Fcorporate.wolt.com%2Foauth2%2Flogin-callback"
           "&response_type=code&code_challenge=abc123&code_challenge_method=S256")
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    print(f"  URL: {page.url[:140]}")
    page.screenshot(path=f"{SHOT}/corp_oauth_1.png")

    print("[2] fill email")
    try:
        page.locator('input[name="email"]').fill(email, timeout=5000)
    except Exception as e:
        print(f"  email input err: {e}")
        # dump inputs
        try:
            for i in page.locator("input").all():
                print(f"    input: name={i.get_attribute('name')} type={i.get_attribute('type')}")
        except Exception:
            pass
    page.wait_for_timeout(800)
    try:
        page.locator('button[type="submit"]').first.click(timeout=5000, no_wait_after=True)
    except Exception as e:
        print(f"  submit err: {e}")
    page.wait_for_timeout(5000)
    print(f"  URL: {page.url[:160]}")
    page.screenshot(path=f"{SHOT}/corp_oauth_2.png")

    # ===== 3. 轮询 mail.tm =====
    print("[3] polling mail.tm for magic link...")
    magic = None
    for attempt in range(30):
        time.sleep(4)
        try:
            r = requests.get("https://api.mail.tm/messages", headers=MAIL_H, timeout=10)
            msgs = r.json().get("hydra:member", [])
            if msgs:
                mid = msgs[0]["id"]
                r2 = requests.get(f"https://api.mail.tm/messages/{mid}", headers=MAIL_H, timeout=10)
                full = r2.json()
                html = (full.get("html") or "") + (full.get("text") or "")
                print(f"  mail: {full.get('subject','')[:70]}")
                links = re.findall(r"https?://[^\s\"'<>]+", html)
                for l in links:
                    if "wolt" in l.lower():
                        magic = l.replace("&amp;", "&")
                        print(f"  !! MAGIC: {magic[:200]}")
                        break
                if not magic:
                    codes = re.findall(r"\b(\d{4,8})\b", html)
                    if codes:
                        magic = codes[0]
                        print(f"  !! CODE: {magic}")
                if magic:
                    break
        except Exception as e:
            print(f"  poll err: {str(e)[:80]}")
        if attempt % 5 == 4:
            print(f"  ...{attempt*4}s")

    # ===== 4. 用 magic link =====
    if magic:
        if magic.startswith("http"):
            print("[4] opening magic link")
            page.goto(magic, timeout=45000, wait_until="domcontentloaded")
        else:
            print("[4] entering code")
            try:
                inputs = page.locator("input").all()
                for i, ch in enumerate(magic[:6]):
                    if i < len(inputs):
                        try: inputs[i].fill(ch, timeout=3000)
                        except Exception: pass
                page.locator('button[type="submit"]').first.click(timeout=4000, no_wait_after=True)
            except Exception as e:
                print(f"  code enter err: {e}")
        for i in range(12):
            page.wait_for_timeout(2500)
            print(f"  ... t={i*2.5}s URL: {page.url[:150]}")
            if CAP["token"] or "login-callback" in page.url or "code=" in page.url:
                break
        page.screenshot(path=f"{SHOT}/corp_oauth_3.png")
    else:
        print("[4] NO MAGIC LINK")

    # ===== 5. 若拿到 code，换 token =====
    m = re.search(r"code=([^&]+)", page.url)
    if m and not CAP["token"]:
        code = m.group(1)
        print(f"[5] exchange code -> token (code={code[:40]}...)")
        # code_challenge 我们用了 abc123，但 PKCE 验证可能在回调时不查（S256 模式下不查就是漏洞）
        r = requests.post("https://authentication.wolt.com/oauth2/token",
                          data={"grant_type": "authorization_code", "code": code,
                                "client_id": "woltatwork-admin",
                                "redirect_uri": "https://corporate.wolt.com/oauth2/login-callback",
                                "code_verifier": "abc123"},
                          timeout=12, headers={"Content-Type": "application/x-www-form-urlencoded"})
        print(f"  HTTP {r.status_code} {r.text[:400]}")
        m2 = re.search(r'"access_token"\s*:\s*"([^"]+)"', r.text)
        if m2:
            CAP["token"] = m2.group(1)
    br.close()

if CAP["token"]:
    json.dump({"access_token": CAP["token"], "email": email},
              open(r"D:\scan\_wolt_hunt\_corp_token.json", "w", encoding="utf-8"), indent=2)
    print(f"\n[OK] CORP TOKEN: {CAP['token'][:60]}...")
else:
    print("\n[FAIL] no corp token")
