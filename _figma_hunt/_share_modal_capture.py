# -*- coding: utf-8 -*-
"""A 打开 Weave 文件(有内容) → 点 Share → 抓分享设置 API 与 UI
目标: 找到 link access 设置入口,确认 Make 文件能否设为私有
"""
import io, re, sys, time, json
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
        if '/api/' in u and not any(x in u for x in ('.png', '.css', '.js', 'sentry', 'figment',
                                                     'metrics', 'analytics', 'web_logger', 'statsig')):
            captured.append({'m': request.method, 'u': u[:220], 'b': (request.post_data or '')[:400]})

    page.on('request', on_request)
    page.goto(BASE + f'/make/{KEY}', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(15000)

    # 找 Share 按钮(任意文本恰为 Share)
    clicked = page.evaluate("""() => {
        const els = [...document.querySelectorAll('button,[role=button],[aria-label]')];
        const t = els.find(e => {
            const txt = (e.textContent || '').trim();
            const aria = (e.getAttribute('aria-label') || '');
            return txt === 'Share' || aria === 'Share' || (txt.length<8 && /^share/i.test(txt));
        });
        if (t) { t.click(); return t.textContent.trim() + '|' + (t.getAttribute('aria-label')||''); }
        return null;
    }""")
    print('clicked:', clicked)
    page.wait_for_timeout(7000)

    body = page.evaluate("() => document.body.innerText.slice(0, 5000)")
    print('\n--- body after share ---')
    print(body[:4500])

    print('\n=== share 相关 API ===')
    for c in captured:
        if any(x in c['u'] for x in ('share', 'permission', 'link', 'access', 'invit')):
            print(c['m'], c['u'])
            if c['b']:
                print('   body:', c['b'][:300])
    try:
        page.screenshot(path='_share_modal2.png')
    except Exception:
        pass
    b.close()
