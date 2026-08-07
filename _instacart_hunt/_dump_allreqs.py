"""dump 点击 Continue 后的所有网络活动 + iframe 检查"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900},
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()

    def block_rise(route):
        if 'icprivate.com' in route.request.url:
            route.fulfill(status=200, content_type='application/grpc-web-text', body='')
        else:
            route.continue_()
    page.route('**/*', block_rise)

    all_reqs = []
    def on_req(r):
        rt = r.resource_type
        all_reqs.append((r.method, r.url, rt))
    page.on('request', on_req)

    page.goto('https://www.instacart.com/signup', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    n_before = len(all_reqs)

    page.fill('input[name=email]', 'test.probe.2026.insta@gmail.com')
    page.wait_for_timeout(1000)
    page.click('button[type=submit]:has-text("Continue")')
    page.wait_for_timeout(8000)

    print('=== 点击后新请求 ===')
    seen = set()
    for m, u, rt in all_reqs[n_before:]:
        host = u.split('/')[2] if '//' in u else '?'
        key = (host, u[:150])
        if key in seen:
            continue
        seen.add(key)
        print(f'[{rt}] {m} {u[:150]}')

    print()
    print('=== iframe 检查 ===')
    frames = page.frames
    for f in frames:
        print(' frame:', f.url[:150])

    # 检查是否有 reCAPTCHA/hCaptcha 元素
    cap = page.evaluate("""() => {
        const sels = ['iframe[src*=recaptcha]', 'iframe[src*=hcaptcha]', '.g-recaptcha', '[class*=captcha]', '[id*=captcha]'];
        const found = [];
        sels.forEach(s => { const els = document.querySelectorAll(s); if (els.length) found.push(s + ' x' + els.length); });
        return found;
    }""")
    print()
    print('=== 验证码元素 ===', cap)

    # console 错误
    console_msgs = []
    page.on('console', lambda m: console_msgs.append((m.type, m.text[:150])))
    br.close()
