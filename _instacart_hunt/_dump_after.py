"""login 页：dump 提交后所有网络活动 + 响应状态"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900},
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()

    def mock_rise(route):
        if 'icprivate.com' in route.request.url:
            route.fulfill(status=200, content_type='application/grpc-web-text', body='AAAAAA==')
        else:
            route.continue_()
    page.route('**/*', mock_rise)

    page.goto('https://www.instacart.com/login', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(9000)

    # 提交前记录已知请求
    seen_before = set()
    def on_resp(r):
        seen_before.add(r.url.split('?')[0])
    page.on('response', on_resp)

    page.fill('input[name=email]', 'test.probe.2026.insta@gmail.com')
    page.wait_for_timeout(1000)
    page.click('button[type=submit]:has-text("Continue")')
    page.wait_for_timeout(8000)

    print('=== 提交后所有请求（含非 graphql） ===')
    # 用 CDP 或重新记录：直接在内存里记录所有请求
    # 简化：重开页面记录全部
    br.close()
