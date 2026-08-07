"""诊断 signup 页面：提交无反应的原因"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=True)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()
    errors = []
    page.on('console', lambda m: errors.append(m.text[:200]) if m.type == 'error' else None)
    reqs = []
    page.on('request', lambda r: reqs.append((r.method, r.url)) if 'graphql' in r.url else None)
    page.goto('https://www.instacart.com/signup', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(6000)

    # dump 页面可见文本
    txt = page.evaluate("""() => {
        const els = [...document.querySelectorAll('label, p, span, div')];
        return els.filter(e => e.offsetParent !== null && (e.innerText||'').trim().length > 3 && (e.innerText||'').trim().length < 120)
           .slice(0, 80).map(e => e.innerText.trim().replace(/\\n/g, ' '));
    }""")
    print('=== 页面可见文本 ===')
    seen = set()
    for t in txt:
        if t not in seen and not t.startswith('{'):
            seen.add(t)
            print(' ', t[:110])
    print()
    print('=== checkbox ===')
    for cb in page.query_selector_all('input[type=checkbox]'):
        print(' checkbox:', (cb.get_attribute('name') or ''), 'checked=', cb.is_checked())
    print()

    # 填邮箱 + 勾 checkbox + 提交
    page.fill('input[name=email]', 'test.probe.2026.insta@gmail.com')
    page.wait_for_timeout(1000)
    for cb in page.query_selector_all('input[type=checkbox]'):
        try:
            if not cb.is_checked():
                cb.check(force=True)
        except Exception:
            pass
    page.click('button[type=submit]:has-text("Continue")')
    page.wait_for_timeout(6000)

    # 提交后新增文本
    txt2 = page.evaluate("""() => [...document.querySelectorAll('p, span')].filter(e => e.offsetParent !== null && (e.innerText||'').trim().length > 0 && (e.innerText||'').trim().length < 150).map(e => e.innerText.trim().replace(/\\n/g, ' '))""")
    new_txt = [t for t in txt2 if t not in seen and t]
    print('=== 提交后新增文本 ===')
    for t in new_txt[:15]:
        print(' ', t[:130])
    print()
    print('=== graphql 请求数:', len(reqs), '===')
    for m, u in reqs[-8:]:
        print(f'  {m} {u[:130]}')
    print()
    print('=== console errors ===')
    for e in errors[:8]:
        print(' ', e[:150])
    br.close()
