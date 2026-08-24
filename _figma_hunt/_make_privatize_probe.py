# -*- coding: utf-8 -*-
"""将 A 的 Make 文件分享设置为私有 → 验证各端点是否仍然公开
流程:
 1. A 打开分享弹窗,把 "Anyone can view" 改为私有(Only people invited)
 2. 抓设置 API(share/v2 或类似)
 3. 验证: 匿名页面 / B file_metadata / B AI端点 / 匿名 preview
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
        if '/api/' in u and any(x in u for x in ('share', 'permission', 'link_access', 'access')):
            captured.append({'m': request.method, 'u': u[:250], 'b': (request.post_data or '')[:500]})

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

    # 找 "Anyone" 下拉
    found = page.evaluate("""() => {
        const els = [...document.querySelectorAll('[role=menuitem],[role=combobox],[data-testid],button')];
        const hits = [];
        for (const el of els) {
            const t = (el.textContent || '').trim();
            if (/anyone/i.test(t)) hits.push({tag: el.tagName, role: el.getAttribute('role'),
                testid: el.getAttribute('data-testid'), text: t.slice(0, 60)});
        }
        return hits.slice(0, 8);
    }""")
    print('anyone elements:', json.dumps(found, ensure_ascii=False)[:800])

    # 点 Anyone 控件
    clicked = page.evaluate("""() => {
        const els = [...document.querySelectorAll('[role=combobox],button,[role=button],[role=listbox]')];
        const t = els.find(e => {
            const txt = (e.textContent || '').trim();
            return /anyone can view/i.test(txt) || (txt === 'Anyone');
        });
        if (t) { t.click(); return t.textContent.trim().slice(0,60); }
        return null;
    }""")
    print('clicked anyone:', clicked)
    page.wait_for_timeout(4000)

    body = page.evaluate("() => document.body.innerText.slice(2000, 6000)")
    print('\n--- body menu ---')
    print(body[:3500])

    # 找 "Only people" 选项
    opt = page.evaluate("""() => {
        const els = [...document.querySelectorAll('[role=menuitem],[role=option],button,[role=button]')];
        const t = els.find(e => {
            const txt = (e.textContent || '').trim();
            return /only people/i.test(txt) || /private/i.test(txt) || /restrict/i.test(txt);
        });
        if (t) { t.click(); return t.textContent.trim().slice(0, 80); }
        return null;
    }""")
    print('clicked private opt:', opt)
    page.wait_for_timeout(5000)

    print('\n=== share API calls ===')
    for c in captured:
        print(c['m'], c['u'])
        if c['b']:
            print('   body:', c['b'][:400])
    b.close()
