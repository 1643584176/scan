"""触发 auth.uber.com 真实登录请求：输入手机号提交，抓 /graphql 请求"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

graphql_reqs = []
with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()

    def on_req(req):
        if 'graphql' in req.url or '/v2/api' in req.url:
            try:
                graphql_reqs.append({'url': req.url, 'method': req.method,
                                     'headers': dict(req.headers),
                                     'body': (req.post_data or '')[:2000]})
            except Exception:
                pass

    page.on('request', on_req)
    page.goto('https://auth.uber.com/v2/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(5000)
    page.screenshot(path='_uber_auth_1.png')

    # 找手机号输入框并输入（韩国号码）
    try:
        inputs = page.locator('input')
        n = inputs.count()
        print(f'input 数量: {n}')
        for i in range(n):
            t = inputs.nth(i)
            print(f'  [{i}] type={t.get_attribute("type")} name={t.get_attribute("name")} placeholder={t.get_attribute("placeholder")} autocomplete={t.get_attribute("autocomplete")}')
        # 输入手机号：选第一个可见的 text/tel 输入
        for i in range(n):
            t = inputs.nth(i)
            if t.is_visible():
                t.fill('01012345678')
                print(f'输入到 [{i}]')
                break
        page.wait_for_timeout(1000)
        page.screenshot(path='_uber_auth_2.png')
        # 找提交按钮
        btns = page.locator('button')
        nb = btns.count()
        for i in range(nb):
            txt = (btns.nth(i).inner_text() or '').strip()[:30]
            print(f'  btn[{i}]: {txt}')
        # 点"继续"按钮（找包含 继续/Continue/다음 的）
        for i in range(nb):
            txt = (btns.nth(i).inner_text() or '').strip()
            if any(k in txt for k in ['继续', 'Continue', '다음', 'Next']):
                btns.nth(i).click()
                print(f'点击按钮[{i}]: {txt}')
                break
        page.wait_for_timeout(6000)
        page.screenshot(path='_uber_auth_3.png')
    except Exception as e:
        print('交互异常:', str(e)[:200])
    br.close()

print(f'\n=== graphql 请求: {len(graphql_reqs)} ===')
for r_ in graphql_reqs:
    print(f'\n{r_["method"]} {r_["url"][:150]}')
    h = {k: v for k, v in r_['headers'].items() if k.startswith('x-uber') or k in ('content-type', 'cookie')}
    for k, v in list(h.items())[:15]:
        print(f'  {k}: {v[:120]}')
    print(f'  body: {r_["body"][:800]}')
