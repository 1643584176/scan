"""完整登录流程抓包：记录 email 登录的所有请求序列 + 页面状态
目标：拿到真实的 grant 提交格式（access_token 换取序列）
"""
import sys, json, time, requests, re, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

LOG = open(r"D:\scan\_wolt_hunt\_login_seq.log", "w", encoding="utf-8")
def log(*a):
    s = " ".join(str(x) for x in a)
    print(s); LOG.write(s + "\n"); LOG.flush()

creds = json.load(open(r"D:\scan\_wolt_hunt\_wolt_creds.json", encoding="utf-8"))
email, mail_token = creds["email"], creds["mail_token"]
MAIL_H = {"Authorization": f"Bearer {mail_token}"}

CAP = {"token": None, "seq": []}

def on_response(resp):
    url, st = resp.url, resp.status
    if any(k in url for k in ("wauth", "auth", "login", "token", "access", "email", "user", "consent")):
        try:
            t = resp.text()[:500]
        except Exception:
            t = ""
        log(f"[RESP] {st} {url[:150]}")
        if t and t.startswith("{"):
            log(f"       {t[:400]}")
        m = re.search(r'"access_token"\s*:\s*"([^"]+)"', t)
        if m and not CAP["token"]:
            CAP["token"] = m.group(1)
            log(f"  !! TOKEN: {m.group(1)[:60]}")

def on_request(req):
    if req.resource_type in ("xhr", "fetch"):
        try:
            body = (req.post_data_buffer.tobytes().decode("utf-8", errors="replace") if req.post_data_buffer else "")
        except Exception:
            body = ""
        CAP["seq"].append(f"{req.method} {req.url} | {body[:300]}")
        if any(k in req.url for k in ("wauth", "auth", "login", "token", "access", "email", "user")):
            log(f"[REQ ] {req.method} {req.url[:150]}")
            if body:
                log(f"       {body[:300]}")

with sync_playwright() as p:
    br = p.chromium.launch(channel="msedge", headless=True, args=["--no-proxy-server"])
    ctx = br.new_context(viewport={"width": 1440, "height": 900}, locale="en-US")
    page = ctx.new_page()
    page.on("response", on_response)
    page.on("request", on_request)

    log("[1] goto wolt.com")
    page.goto("https://wolt.com/en/fin", timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    try: page.locator('[data-test-id="decline-button"]').click(timeout=3000)
    except Exception: pass
    page.wait_for_timeout(1000)

    log("[2] click Log in")
    page.locator('[data-test-id="UserStatus.Login"]').click(timeout=8000)
    page.wait_for_timeout(3000)

    log("[3] fill email")
    page.locator('input[type="email"]').first.fill(email, timeout=5000)
    page.wait_for_timeout(800)
    # dump 页面可见文本
    try:
        txt = page.inner_text("body")[:600]
        log(f"[UI] {txt[:500]}")
    except Exception as e:
        log(f"[UI] err {e}")

    log("[4] click Continue")
    try:
        page.locator('[data-test-id="StepMethodSelect.NextButton"]').click(timeout=5000, no_wait_after=True)
    except Exception as e:
        log(f"  NextButton fail: {e}")
        # 备选按钮
        try:
            page.locator('button[type="submit"]').first.click(timeout=4000, no_wait_after=True)
        except Exception:
            pass

    # 持续观察 UI 变化 + 轮询邮件
    log("[5] observe + poll mail")
    code = None
    for attempt in range(25):
        time.sleep(4)
        # 页面状态
        try:
            cur = page.url[:100]
            body_txt = page.inner_text("body")[:300].replace("\n", " | ")
        except Exception:
            cur, body_txt = "?", "?"
        if attempt % 3 == 0:
            log(f"  t={attempt*4}s url={cur}")
            log(f"  UI: {body_txt[:250]}")
        # 邮件
        try:
            r = requests.get("https://api.mail.tm/messages", headers=MAIL_H, timeout=10)
            msgs = r.json().get("hydra:member", [])
            if msgs:
                mid = msgs[0]["id"]
                r2 = requests.get(f"https://api.mail.tm/messages/{mid}", headers=MAIL_H, timeout=10)
                full = r2.json()
                html = (full.get("html") or "") + (full.get("text") or "")
                log(f"  MAIL: {full.get('subject','')[:80]}")
                codes = re.findall(r"\b(\d{4,8})\b", html)
                if codes:
                    code = codes[0]
                    log(f"  !! CODE: {code}")
                    break
        except Exception as e:
            log(f"  poll err: {str(e)[:80]}")

    if code:
        log("[6] enter code")
        try:
            inputs = page.locator('input:not([type="email"])').all()
            for i, d in enumerate(code[:6]):
                if i < len(inputs):
                    try: inputs[i].fill(d, timeout=3000)
                    except Exception: pass
            page.wait_for_timeout(2000)
            try:
                page.locator('button[type="submit"]').first.click(timeout=4000, no_wait_after=True)
            except Exception:
                pass
        except Exception as e:
            log(f"  enter code err: {e}")
        page.wait_for_timeout(5000)

    log("[7] wait token")
    for _ in range(15):
        page.wait_for_timeout(2500)
        if CAP["token"]:
            break
    log(f"final URL: {page.url[:150]}")
    page.screenshot(path=r"D:\scan\_wolt_hunt\_login_seq_final.png")

    # localStorage token
    if not CAP["token"]:
        try:
            items = page.evaluate("() => Object.entries(localStorage)")
            for k, v in items:
                if any(t in k.lower() for t in ("token", "auth", "session")):
                    log(f"  LS[{k}] = {str(v)[:200]}")
                    m = re.search(r'"access_token"\s*:\s*"([^"]+)"', str(v))
                    if m: CAP["token"] = m.group(1)
        except Exception as e:
            log(f"  LS err: {e}")
    br.close()

log("\n==== ALL API CALLS ====")
for s in CAP["seq"]:
    log(s)
if CAP["token"]:
    json.dump({"access_token": CAP["token"]}, open(r"D:\scan\_wolt_hunt\_wolt_token.json", "w", encoding="utf-8"), indent=2)
    log(f"[OK] token: {CAP['token'][:60]}")
else:
    log("[FAIL] no token")
LOG.close()
