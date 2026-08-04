# -*- coding: utf-8 -*-
"""自动化注册：生成临时邮箱 → 填表 → 看下一步要什么"""
import sys, json, os, time, requests, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

SHOT = 'D:/scan/_wolt_hunt/_payment_shots'
os.makedirs(SHOT, exist_ok=True)

# ===== Step 0: 生成临时邮箱 =====
print('=== Creating temp email ===')
try:
    # guerrillamail
    r = requests.get('https://api.guerrillamail.com/ajax.php?f=get_email_address&ip=127.0.0.1&agent=Mozilla', timeout=15)
    gm = r.json()
    email = gm['email_addr']
    sid = gm['sid_token']
    print(f'Temp email: {email}')
    print(f'SID: {sid[:20]}...')
except Exception as e:
    print(f'guerrillamail fail: {e}, trying mail.tm...')
    # mail.tm fallback
    try:
        r = requests.post('https://api.mail.tm/accounts', json={'address': 'pccp' + str(int(time.time()))[-6:] + '@bugfoo.com', 'password': 'Test1234!'}, timeout=15)
        acc = r.json()
        email = acc['address']
        r2 = requests.post('https://api.mail.tm/token', json={'address': email, 'password': 'Test1234!'}, timeout=15)
        token = r2.json()['token']
        print(f'mail.tm email: {email}')
    except Exception as e2:
        print(f'mail.tm fail: {e2}')
        email = f'pccp_h1_{int(time.time())}@gmail.com'
        print(f'fallback: {email} (manual)')

# ===== Step 1: 打开 Wolt 注册流程 =====
with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=True, args=['--no-proxy-server'])
    ctx = br.new_context(viewport={'width': 1440, 'height': 900}, locale='en-US')
    page = ctx.new_page()
    
    page.goto('https://wolt.com/en/fin', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    try: page.locator('[data-test-id="decline-button"]').click(timeout=3000)
    except: pass
    page.wait_for_timeout(2000)
    
    # 点 Sign up
    page.locator('[data-test-id="UserStatus.Signup"]').click(timeout=5000)
    page.wait_for_timeout(5000)
    page.screenshot(path=f'{SHOT}/_reg_01_signup_modal.png')
    
    # 输入 email
    try:
        email_input = page.locator('input[type="email"], input[name="email"]').first
        email_input.fill(email, timeout=5000)
        print(f'filled email: {email}')
    except Exception as e:
        print(f'email fill fail: {e}')
    
    page.wait_for_timeout(2000)
    page.screenshot(path=f'{SHOT}/_reg_02_email_filled.png')
    
    # 看出现了什么按钮
    btns = page.evaluate("""() => {
        const out = [];
        for (const b of document.querySelectorAll('button, [role="button"]')) {
            const t = (b.textContent || '').trim();
            if (t && b.offsetParent !== null) out.push({
                text: t.slice(0,60),
                type: b.type || '',
                testid: b.getAttribute('data-test-id') || '',
                disabled: b.disabled || false
            });
        }
        return out;
    }""")
    print('\nVisible buttons after email:')
    for b in btns:
        flag = ' [DISABLED]' if b['disabled'] else ''
        print(f'  "{b["text"]}" testid={b["testid"]}{flag}')
    
    # 找 Continue/Next 按钮
    for sel in ['button:has-text("Continue")', 'button:has-text("Next")', '[data-test-id*="continue" i]', '[data-test-id*="submit" i]', 'button[type="submit"]']:
        try:
            btn = page.locator(sel).first
            if btn.count() and btn.is_visible():
                btn.click(timeout=3000)
                print(f'clicked: {sel}')
                break
        except: pass
    
    page.wait_for_timeout(5000)
    page.screenshot(path=f'{SHOT}/_reg_03_after_continue.png')
    
    # 看现在的表单
    new_inputs = page.evaluate("""() => {
        const out = [];
        for (const i of document.querySelectorAll('input, select')) {
            if (i.offsetParent !== null) {
                out.push({
                    tag: i.tagName,
                    type: i.type || '',
                    placeholder: i.placeholder || '',
                    name: i.name || '',
                    testid: i.getAttribute('data-test-id') || '',
                    required: i.required
                });
            }
        }
        return out;
    }""")
    print('\nInputs after continue:')
    for inp in new_inputs:
        print(f'  {inp["tag"]} type={inp["type"]} placeholder="{inp["placeholder"]}" name="{inp["name"]}" testid="{inp["testid"]}" required={inp["required"]}')
    
    # 按钮
    btns2 = page.evaluate("""() => {
        const out = [];
        for (const b of document.querySelectorAll('button, [role="button"]')) {
            const t = (b.textContent || '').trim();
            if (t && b.offsetParent !== null) out.push(t.slice(0,60));
        }
        return out;
    }""")
    print('\nButtons after continue:', list(set(btns2)))
    
    # 可见文字
    visible = page.evaluate("""() => {
        const t = [];
        for (const el of document.querySelectorAll('h1,h2,h3,p,span,label,div')) {
            if (el.offsetParent !== null && el.children.length === 0) {
                const txt = el.textContent.trim();
                if (txt && txt.length > 3 && txt.length < 100) t.push(txt);
            }
        }
        return t.slice(0, 20);
    }""")
    print('\nVisible text:')
    for v in visible:
        print(f'  "{v}"')
    
    print(f'\nURL: {page.url}')
    br.close()
