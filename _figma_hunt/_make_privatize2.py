# -*- coding: utf-8 -*-
"""用 data-testid 操作 file-audience-row → 改为 Only people
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
        if '/api/' in u and any(x in u for x in ('share', 'permission', 'link_access', 'audience', 'access')):
            captured.append({'m': request.method, 'u': u[:250], 'b': (request.post_data or '')[:600]})

    page.on('request', on_request)
    page.goto(BASE + f'/make/{KEY}', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(15000)
    page.evaluate("""() => {
        const els = [...document.querySelectorAll('button,[role=button]')];
        const t = els.find(e => (e.textContent||'').trim() === 'Share');
        if (t) t.click();
    }""")
    page.wait_for_timeout(5000)

    # 点 file-audience-row
    r = page.evaluate("""() => {
        const el = document.querySelector('[data-testid="file-audience-row"]');
        if (!el) return 'not found';
        el.click();
        return 'clicked: ' + (el.textContent||'').trim().slice(0,60);
    }""")
    print(r)
    page.wait_for_timeout(4000)

    # 列出菜单选项
    opts = page.evaluate("""() => {
        const out = [];
        for (const el of document.querySelectorAll('[role=menuitem],[role=option],button')) {
            const t = (el.textContent || '').trim();
            if (t && t.length < 80) out.push(t);
        }
        return [...new Set(out)].slice(0, 30);
    }""")
    print('menu options:', json.dumps(opts, ensure_ascii=False))

    # 找 Only people invited / Restrict
    r2 = page.evaluate("""() => {
        const els = [...document.querySelectorAll('[role=menuitem],[role=option],button,[role=button]')];
        for (const t of els) {
            const txt = (t.textContent || '').trim();
            if (/only people/i.test(txt)) { t.click(); return 'clicked: ' + txt.slice(0,80); }
        }
        return 'not found only people';
    }""")
    print(r2)
    page.wait_for_timeout(5000)

    body = page.evaluate("() => document.body.innerText.slice(0, 4000)")
    print('\n--- body ---')
    print(body[:3500])

    print('\n=== API calls ===')
    for c in captured:
        print(c['m'], c['u'])
        if c['b']:
            print('   body:', c['b'][:500])
    b.close()
