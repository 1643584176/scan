# -*- coding: utf-8 -*-
"""yopmail 验证：读取逻辑诊断 + Wolt OAuth 邮件轮询"""
import sys, json, time, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

login_name = "pccp" + str(int(time.time()))[-6:]
email = f"{login_name}@yopmail.com"
print(f"[1] yopmail: {email}", flush=True)

CAP = {"token": None, "authed": False}

def on_response(resp):
    if "authentication" in resp.url:
        try:
            t = resp.text()[:500]
            if t.startswith("{"):
                print(f"  [RESP] {resp.status} {resp.url[:110]} -> {t[:180]}", flush=True)
                m = re.search(r'"access_token"\s*:\s*"([^"]+)"', t)
                if m:
                    CAP["token"] = m.group(1)
        except Exception:
            pass

with sync_playwright() as p:
    br = p.chromium.launch(channel="msedge", headless=True, args=["--no-proxy-server"])
    ctx = br.new_context(viewport={"width": 1440, "height": 900}, locale="en-US")
    page = ctx.new_page()
    page.on("response", on_response)

    # ===== yopmail 主站建会话 =====
    try:
        page.goto("https://yopmail.com/", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        print("[0] yopmail.com OK", flush=True)
    except Exception as e:
        print(f"[0] yopmail.com ERR: {str(e)[:100]}", flush=True)

    # ===== Wolt OAuth 登录 =====
    print("[2] OAuth authorize -> login", flush=True)
    url = ("https://authentication.wolt.com/oauth2/authorize?client_id=woltatwork-admin"
           "&redirect_uri=https%3A%2F%2Fcorporate.wolt.com%2Foauth2%2Flogin-callback"
           "&response_type=code&code_challenge=abc123&code_challenge_method=S256")
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    page.locator('input[name="email"]').fill(email, timeout=5000)
    page.wait_for_timeout(800)
    page.locator('button[type="submit"]').first.click(timeout=5000, no_wait_after=True)
    page.wait_for_timeout(4000)
    print(f"  URL: {page.url[:130]}", flush=True)

    # ===== yopmail 轮询（带刷新）=====
    print("[3] Polling yopmail...", flush=True)
    magic = None
    for attempt in range(20):
        time.sleep(6)
        try:
            page.goto(f"https://yopmail.com/en/inbox?login={login_name}", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            # 检查是否有邮件条目（#mails 区域）或刷新按钮
            has_mail = page.evaluate('''() => {
                const m = document.querySelectorAll('#mails .lm');
                const err = document.querySelector('#e_maillist, .esl');
                const refresh = document.querySelector('#refresh');
                const ifmail = document.querySelector('#ifmail');
                return {mails: m.length, err: err ? err.textContent.slice(0,80) : null, refresh: !!refresh, ifmail: !!ifmail};
            }''')
            print(f"  inbox({attempt}): {has_mail}", flush=True)
            if has_mail["mails"] > 0:
                # 点第一条
                try:
                    page.locator("#mails .lm").first.click(timeout=4000)
                    page.wait_for_timeout(2500)
                except Exception:
                    pass
                # 读 iframe 内容
                try:
                    frame = page.frame_locator("iframe#ifmail")
                    txt = frame.locator("body").inner_text(timeout=6000)
                    print(f"  MAIL TEXT: {re.sub(chr(10),' | ',txt)[:300]}", flush=True)
                    links = re.findall(r"https?://[^\s\"'<>]+", txt)
                    for l in links:
                        if "wolt" in l.lower():
                            magic = l.replace("&amp;", "&")
                            print(f"  !! MAGIC: {magic[:180]}", flush=True)
                            break
                    if magic:
                        break
                except Exception as e:
                    print(f"  iframe ERR: {str(e)[:80]}", flush=True)
            else:
                # 点刷新
                try:
                    page.locator("#refresh").click(timeout=3000)
                    page.wait_for_timeout(2500)
                except Exception:
                    pass
        except Exception as e:
            print(f"  inbox ERR: {str(e)[:100]}", flush=True)

    if magic:
        print("[4] Opening magic link...", flush=True)
        page.goto(magic, timeout=45000, wait_until="domcontentloaded")
        for i in range(10):
            page.wait_for_timeout(2500)
            print(f"  ... t={i*2.5}s URL: {page.url[:140]}", flush=True)
            if CAP["token"] or "callback" in page.url or "code=" in page.url:
                break
        print(f"  final URL: {page.url[:160]}", flush=True)
    else:
        print("[4] NO MAIL", flush=True)

    br.close()

if CAP["token"]:
    json.dump({"access_token": CAP["token"]}, open(r"D:\scan\_wolt_hunt\_wolt_token.json", "w", encoding="utf-8"), indent=2)
    print(f"\n[OK] TOKEN: {CAP['token'][:60]}...", flush=True)
else:
    print("\n[FAIL] no token", flush=True)
