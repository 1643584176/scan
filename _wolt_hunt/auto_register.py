# -*- coding: utf-8 -*-
"""全自动 Wolt 注册：mail.tm 邮箱 + Playwright 填表 + 收验证码"""
import sys, json, os, time, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

SHOT = 'D:/scan/_wolt_hunt/_payment_shots'
os.makedirs(SHOT, exist_ok=True)
CREDS_FILE = 'D:/scan/_wolt_hunt/_wolt_creds.json'

# ===== 1. mail.tm 创建邮箱（自动获取当前可用域名）=====
print('[1] Creating mail.tm account...')
MAIL_PASS = 'PccpTest123!'
try:
    # 获取当前可用域名
    dr = requests.get('https://api.mail.tm/domains', timeout=10)
    domains = dr.json().get('hydra:member', [])
    domain = domains[0]['domain'] if domains else 'web-library.net'
    print(f'  domain: {domain}')
    
    ts = str(int(time.time()))[-8:]
    email_addr = f'pccp{ts}@{domain}'
    r = requests.post('https://api.mail.tm/accounts', json={
        'address': email_addr,
        'password': MAIL_PASS
    }, timeout=15)
    if r.status_code != 201:
        print(f'  create FAIL: {r.status_code} {r.text[:200]}')
        sys.exit(1)
    acc = r.json()
    email = acc['address']
    print(f'  email: {email}')
    
    r2 = requests.post('https://api.mail.tm/token', json={
        'address': email, 'password': MAIL_PASS
    }, timeout=15)
    mail_token = r2.json()['token']
    print(f'  token: {mail_token[:30]}...')
    MAIL_HEADERS = {'Authorization': f'Bearer {mail_token}'}
except Exception as e:
    print(f'  mail.tm FAIL: {e}')
    sys.exit(1)

# ===== 2. Playwright 注册 =====
REQS = []
def hook(route):
    req = route.request
    if req.resource_type in ('xhr', 'fetch'):
        body = (req.post_data or '')[:500]
        REQS.append({'m': req.method, 'u': req.url, 'body': body})
        # 检查是否是注册/验证相关API
        if any(k in req.url for k in ('auth', 'login', 'signup', 'register', 'verify', 'token', 'session', 'user')):
            print(f'  [API] {req.method} {req.url[:150]}')
            if body:
                print(f'        body: {body[:200]}')
    route.continue_()

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=True, args=['--no-proxy-server', '--disable-web-security'])
    ctx = br.new_context(viewport={'width': 1440, 'height': 900}, locale='en-US')
    page = ctx.new_page()
    page.route('**/*', hook)
    
    # 首页
    print('[2] Opening Wolt...')
    page.goto('https://wolt.com/en/fin', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    try: page.locator('[data-test-id="decline-button"]').click(timeout=3000)
    except: pass
    page.wait_for_timeout(1500)
    
    # 点 Sign up
    print('[3] Clicking Sign up...')
    page.locator('[data-test-id="UserStatus.Signup"]').click(timeout=5000)
    page.wait_for_timeout(4000)
    page.screenshot(path=f'{SHOT}/reg_1_modal.png')
    
    # 填邮箱
    print('[4] Filling email...')
    page.locator('input[type="email"]').first.fill(email, timeout=5000)
    page.wait_for_timeout(1500)
    page.screenshot(path=f'{SHOT}/reg_2_filled.png')
    
    # 点 Continue（不等待导航，Wolt 可能重定向到 auth 子域名）
    print('[5] Clicking Continue...')
    page.locator('[data-test-id="StepMethodSelect.NextButton"]').click(timeout=5000, no_wait_after=True)
    
    # 等页面稳定
    for _ in range(8):
        page.wait_for_timeout(2000)
        url = page.url
        if 'error' not in url and 'chrome-error' not in url:
            break
    
    page.screenshot(path=f'{SHOT}/reg_3_after_continue.png')
    print(f'  URL: {page.url[:150]}')
    
    # 如果是 chrome-error，说明 Wolt auth 服务器不可达
    if 'chrome-error' in page.url or 'error' in page.url.lower():
        # 尝试用 page.evaluate 关闭错误页并回到前一页
        print('  !! Auth server unreachable, trying alternative approach...')
        # 可能 Wolt 反爬，尝试回到首页看是否实际已有 session
        page.goto('https://wolt.com/en/fin', timeout=15000, wait_until='domcontentloaded')
        page.wait_for_timeout(5000)
        page.screenshot(path=f'{SHOT}/reg_3b_back_to_home.png')
    
    # 看页面内容
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
    
    btns = page.evaluate("""() => [...document.querySelectorAll('button,[role="button"]')]
        .filter(b => b.offsetParent !== null)
        .map(b => ({t: b.textContent.trim().slice(0,50), tid: b.getAttribute('data-test-id')||''}))
        .filter(b => b.t)
    """)
    print(f'  Buttons: {btns}')
    
    # 看是验证码页面还是错误页面
    title = page.title()
    print(f'  Title: {title}')
    
    # 即使页面出错，Wolt 后端可能已经发了邮件，继续收验证码
    if 'error' in page.url.lower() or 'time' in title.lower() or 'chrome-error' in page.url:
        print('  !! Browser shows error but email may have been sent, continuing...')
    
    # ===== 3. 收验证码 =====
    # 等几秒让邮件到达
    print('[6] Waiting for verification email...')
    code = None
    for attempt in range(12):  # 最多等60秒
        time.sleep(5)
        try:
            r = requests.get('https://api.mail.tm/messages', headers=MAIL_HEADERS, timeout=10)
            msgs = r.json().get('hydra:member', [])
            if msgs:
                msg = msgs[0]
                subject = msg.get('subject', '')
                print(f'  Got email: "{subject}"')
                # 获取邮件内容
                msg_id = msg['id']
                r2 = requests.get(f'https://api.mail.tm/messages/{msg_id}', headers=MAIL_HEADERS, timeout=10)
                html = r2.json().get('html', '') or r2.json().get('text', '')
                # 提取验证码（4-6位数字）
                import re
                codes = re.findall(r'\b(\d{4,6})\b', html)
                if codes:
                    code = codes[0]
                    print(f'  !! Code: {code}')
                    break
                # 也搜索纯文本
                codes2 = re.findall(r'\b(\d{4,6})\b', r2.json().get('text', ''))
                if codes2:
                    code = codes2[0]
                    print(f'  !! Code: {code}')
                    break
        except Exception as e:
            print(f'  poll err: {str(e)[:80]}')
    
    if not code:
        print('  !! No code received, saving state for manual')
        with open(CREDS_FILE, 'w') as f:
            json.dump({'email': email, 'password': MAIL_PASS, 'mail_token': mail_token}, f)
        page.screenshot(path=f'{SHOT}/reg_no_code.png')
        br.close()
        sys.exit(1)
    
    # ===== 4. 填验证码 =====
    print('[7] Entering verification code...')
    # 验证码输入通常是多个单个数字输入框，或者是单个输入框
    code_inputs = page.locator('input[type="text"], input[type="number"], input:not([type="email"]):not([type="password"])').all()
    if len(code_inputs) >= 4:
        # 多个独立输入框
        for i, digit in enumerate(code[:6]):
            try:
                code_inputs[i].fill(digit, timeout=3000)
            except: pass
    else:
        # 单个输入框
        try:
            page.locator('input[type="text"], input[type="number"]').first.fill(code, timeout=5000)
        except: pass
    
    page.wait_for_timeout(2000)
    page.screenshot(path=f'{SHOT}/reg_4_code_entered.png')
    
    # 找 Continue/Submit 按钮
    for sel in ['button:has-text("Continue")', 'button:has-text("Next")', 'button:has-text("Submit")', 'button:has-text("Verify")']:
        try:
            page.locator(sel).first.click(timeout=3000)
            print(f'  clicked: {sel}')
            break
        except: pass
    
    page.wait_for_timeout(8000)
    page.screenshot(path=f'{SHOT}/reg_5_after_code.png')
    print(f'  URL: {page.url[:150]}')
    print(f'  Title: {page.title()}')
    
    # 看是否需要填名字等其他信息
    inputs2 = page.evaluate("""() => {
        const out = [];
        for (const i of document.querySelectorAll('input')) {
            if (i.offsetParent !== null) out.push({
                type: i.type, name: i.name || '', placeholder: i.placeholder || '',
                testid: i.getAttribute('data-test-id') || ''
            });
        }
        return out;
    }""")
    print(f'  Post-code inputs: {inputs2}')
    
    btns2 = page.evaluate("""() => [...document.querySelectorAll('button,[role="button"]')]
        .filter(b => b.offsetParent !== null)
        .map(b => b.textContent.trim().slice(0,50))
        .filter(Boolean)
    """)
    print(f'  Post-code buttons: {btns2}')
    
    # 保存最终状态
    page.screenshot(path=f'{SHOT}/reg_final.png')
    br.close()
    print(f'\n[DONE] email={email}')
    print(f'Total API requests: {len(REQS)}')
