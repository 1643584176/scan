"""拦截 rpc-rise 配置请求，尝试让 React hydration 恢复"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=True)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()

    # 拦截 rpc-rise 域名：返回空 gRPC-web 响应
    def block_rise(route):
        url = route.request.url
        if 'icprivate.com' in url:
            route.fulfill(status=200, content_type='application/grpc-web-text', body='')
        else:
            route.continue_()
    page.route('**/*', block_rise)

    reqs = []
    page.on('request', lambda r: reqs.append(r.url) if 'graphql' in r.url else None)
    console_errors = []
    page.on('console', lambda m: console_errors.append(m.text[:150]) if m.type == 'error' else None)

    page.goto('https://www.instacart.com/signup', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(10000)

    # 检查按钮是否可交互（事件绑定）
    btn_ok = page.evaluate("""() => {
        const btn = [...document.querySelectorAll('button')].find(b => (b.innerText||'').trim() === 'Continue');
        if (!btn) return 'NO_BUTTON';
        return 'found: ' + btn.outerHTML.slice(0, 150);
    }""")
    print('按钮状态:', btn_ok)

    # 尝试填邮箱提交
    try:
        page.fill('input[name=email]', 'test.probe.2026.insta@gmail.com')
        page.wait_for_timeout(1000)
        page.click('button[type=submit]:has-text("Continue")')
        page.wait_for_timeout(6000)
        print('已点击 Continue')
    except Exception as e:
        print('交互 err:', str(e)[:120])

    print()
    print('=== graphql 请求 ===')
    for u in reqs[-10:]:
        print(' ', u[:130])
    print()
    print('=== console errors ===')
    for e in console_errors[:8]:
        print(' ', e)
    br.close()
