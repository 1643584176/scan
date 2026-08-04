# -*- coding: utf-8 -*-
"""方案：用 Log in 替代 Sign up（可能只发邮箱验证码，不走 SMS）"""
import sys, json, os, time, requests, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

SHOT = 'D:/scan/_wolt_hunt/_payment_shots'
os.makedirs(SHOT, exist_ok=True)

# ===== 1. 创建临时邮箱 =====
print('[1] Creating mail.tm...')
MAIL_PASS = 'PccpTest123!'
dr = requests.get('https://api.mail.tm/domains', timeout=10)
domain = dr.json()['hydra:member'][0]['domain']
ts = str(int(time.time()))[-8:]
email_addr = f'pccp{ts}@{domain}'
r = requests.post('https://api.mail.tm/accounts', json={'address': email_addr, 'password': MAIL_PASS}, timeout=15)
email = r.json()['address']
r2 = requests.post('https://api.mail.tm/token', json={'address': email, 'password': MAIL_PASS}, timeout=15)
mail_token = r2.json()['token']
MAIL_HEADERS = {'Authorization': f'Bearer {mail_token}'}
print(f'  email: {email}')

# ===== 2. Wolt LOG IN 流程（不是 sign up）=====
REQS = []
def hook(route):
    req = route.request
    if req.resource_type in ('xhr', 'fetch'):
        try:
            body = (req.post_data_buffer.tobytes().decode('utf-8', errors='replace') if req.post_data_buffer else '')[:500]
        except:
            body = ''
        REQS.append({'m': req.method, 'u': req.url, 'body': body})
        if any(k in req.url for k in ('auth', 'login', 'signup', 'register', 'verify', 'token', 'session')):
            print(f'  [API] {req.method} {req.url[:150]}')
            if body:
                print(f'        {body[:200]}')
    route.continue_()

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=True, args=['--no-proxy-server'])
    ctx = br.new_context(viewport={'width': 1440, 'height': 900}, locale='en-US')
    page = ctx.new_page()
    page.route('**/*', hook)
    
    print('[2] Opening Wolt...')
    page.goto('https://wolt.com/en/fin', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    try: page.locator('[data-test-id="decline-button"]').click(timeout=3000)
    except: pass
    page.wait_for_timeout(1000)
    
    # 点击 "Log in"（不是 Sign up）
    print('[3] Clicking Log in...')
    page.locator('[data-test-id="UserStatus.Login"]').click(timeout=5000)
    page.wait_for_timeout(4000)
    page.screenshot(path=f'{SHOT}/login_1.png')
    
    # 填邮箱
    print('[4] Filling email...')
    page.locator('input[type="email"]').first.fill(email, timeout=5000)
    page.wait_for_timeout(2000)
    page.screenshot(path=f'{SHOT}/login_2.png')
    
    # 看按钮
    btns = page.evaluate("""() => [...document.querySelectorAll('button,[role="button"]')]
        .filter(b => b.offsetParent !== null)
        .map(b => ({t: b.textContent.trim().slice(0,50), tid: b.getAttribute('data-test-id')||'', d: b.disabled}))
    """)
    print(f'  Buttons: {btns}')
    
    # 点 Continue（如果有）
    try:
        page.locator('[data-test-id="StepMethodSelect.NextButton"]').click(timeout=5000, no_wait_after=True)
        print('[5] Clicked Continue (LOGIN)')
    except:
        print('[5] No Continue button found')
    
    # 等待
    for _ in range(8):
        page.wait_for_timeout(2000)
        url = page.url
        if 'error' not in url and 'chrome-error' not in url:
            break
    page.screenshot(path=f'{SHOT}/login_3.png')
    print(f'  URL: {page.url[:150]}')
    print(f'  Title: {page.title()}')
    
    # 看当前表单
    inputs = page.evaluate("""() => {
        const out = [];
        for (const i of document.querySelectorAll('input')) {
            if (i.offsetParent !== null) out.push({
                type: i.type, name: i.name || '', placeholder: i.placeholder || '',
                testid: i.getAttribute('data-test-id') || '', maxLength: i.maxLength
            });
        }
        return out;
    }""")
    print(f'  Inputs: {inputs}')
    
    # ===== 3. 收验证码 =====
    print('[6] Polling email...')
    code = None
    for attempt in range(15):
        time.sleep(4)
        try:
            r = requests.get('https://api.mail.tm/messages', headers=MAIL_HEADERS, timeout=10)
            msgs = r.json().get('hydra:member', [])
            if msgs:
                msg = msgs[0]
                subject = msg.get('subject', '')
                print(f'  Got: "{subject}"')
                msg_id = msg['id']
                r2 = requests.get(f'https://api.mail.tm/messages/{msg_id}', headers=MAIL_HEADERS, timeout=10)
                body = r2.json()
                html = body.get('html', '') or ''
                text = body.get('text', '') or ''
                # 提取数字验证码
                codes = re.findall(r'\b(\d{4,8})\b', html + text)
                # 提取链接
                links = re.findall(r'https?://[^\s"<>]+', html + text)
                if codes:
                    code = codes[0]
                    print(f'  !! Code: {code}')
                    break
                if links:
                    print(f'  Links: {links[:3]}')
        except Exception as e:
            print(f'  poll: {str(e)[:60]}')
    
    if code:
        print('[7] Entering code...')
        code_inputs = page.locator('input[type="text"], input[type="number"], input:not([type="email"])').all()
        for i, digit in enumerate(code[:6]):
            try: code_inputs[i].fill(digit, timeout=3000)
            except: pass
        page.wait_for_timeout(2000)
        page.screenshot(path=f'{SHOT}/login_4_code.png')
    else:
        print('  !! No email received in 60s')
    
    page.screenshot(path=f'{SHOT}/login_final.png')
    br.close()
    print(f'\n[DONE] email={email}  API calls={len(REQS)}')
    for r in REQS:
        if any(k in r['u'] for k in ('auth', 'login', 'token')):
            print(f'  {r["m"]} {r["u"][:150]}')
