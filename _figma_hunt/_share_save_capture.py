# -*- coding: utf-8 -*-
"""A 打开 Weave 文件 → Share 弹窗 → 把 Audience 改为 Only people → Save
抓取所有非 GET 请求, 拿到分享设置保存 API 的真实形态
"""
import io, json, sys, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
KEY = "5zb5YkoxMa09KpqOyuLcHD"


def raw_cookie(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


def cookies_for_browser(raw):
    result = []
    for pair in raw.split('; '):
        if '=' not in pair:
            continue
        name, value = pair.split('=', 1)
        item = {'name': name, 'value': value, 'secure': True, 'sameSite': 'Lax'}
        if name.startswith('__Host-'):
            item['url'] = BASE
        else:
            item.update({'domain': '.figma.com', 'path': '/'})
        result.append(item)
    return result


captured = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': 1500, 'height': 900})
    ctx.add_cookies(cookies_for_browser(raw_cookie('ws_cookie_A_new.txt')))
    page = ctx.new_page()

    def on_request(request):
        u = request.url
        if '/api/' in u and request.method != 'GET' and not any(
                x in u for x in ('.png', '.css', '.js', 'sentry', 'metrics', 'statsig', 'figment')):
            captured.append({'m': request.method, 'u': u[:260], 'b': (request.post_data or '')[:800]})

    page.on('request', on_request)
    page.goto(BASE + f'/make/{KEY}', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(15000)

    # 点 Share
    page.evaluate("""() => {
        const els = [...document.querySelectorAll('button,[role=button]')];
        const t = els.find(e => (e.textContent||'').trim() === 'Share');
        if (t) t.click();
    }""")
    page.wait_for_timeout(5000)

    # 点 audience 行
    page.evaluate("""() => {
        const el = document.querySelector('[data-testid="file-audience-row"]');
        if (el) el.click();
    }""")
    page.wait_for_timeout(3000)

    # 选 Only people invited
    r = page.evaluate("""() => {
        const els = [...document.querySelectorAll('[role=menuitem],[role=option],button,[role=button]')];
        const t = els.find(e => {
            const txt = (e.textContent || '').trim();
            return /only people/i.test(txt);
        });
        if (t) { t.click(); return 'clicked: ' + t.textContent.trim().slice(0,80); }
        return null;
    }""")
    print(r)
    page.wait_for_timeout(3000)

    # 找并点 Save / Done 按钮
    r2 = page.evaluate("""() => {
        const els = [...document.querySelectorAll('button,[role=button]')];
        const t = els.find(e => {
            const txt = (e.textContent || '').trim();
            return txt === 'Save' || txt === 'Done' || /^save$/i.test(txt);
        });
        if (t) { t.click(); return 'clicked: ' + txt; }
        return null;
    }""")
    print(r2)
    page.wait_for_timeout(6000)

    print('\n=== WRITE API calls ===')
    for c in captured:
        print(c['m'], c['u'])
        if c['b']:
            print('   body:', c['b'][:600])
    print('total:', len(captured))
    b.close()
