"""login 页：dump 提交后所有网络活动 + 响应状态（完整版）"""
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

    all_reqs = []  # (seq, method, url, status)
    seq = [0]
    def on_req(r):
        seq[0] += 1
        all_reqs.append((seq[0], r.method, r.url, None))
    page.on('request', on_req)
    def on_resp(r):
        for i, (s, m, u, st) in enumerate(all_reqs):
            if st is None and u == r.url:
                all_reqs[i] = (s, m, u, r.status)
                break
    page.on('response', on_resp)

    page.goto('https://www.instacart.com/login', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(9000)
    n_before = seq[0]

    page.fill('input[name=email]', 'test.probe.2026.insta@gmail.com')
    page.wait_for_timeout(1200)
    page.click('button[type=submit]:has-text("Continue")')
    page.wait_for_timeout(9000)

    print(f'提交前请求数: {n_before}, 提交后新增: {seq[0] - n_before}')
    print()
    for s, m, u, st in all_reqs[n_before:]:
        print(f'#{s} [{st}] {m} {u[:160]}')
    br.close()
