# -*- coding: utf-8 -*-
"""A 打开自己的 Make 文件 → 找分享设置(link access) → 尝试设为私有
"""
import io, re, sys, time, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
KEY = "QooNP4ZnOkwGbudKlPX635"   # A 刚创建的新 Make 文件


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


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': 1500, 'height': 900})
    ctx.add_cookies(cookies_for_browser(raw_cookie('ws_cookie_A_new.txt')))
    page = ctx.new_page()
    page.goto(BASE + f'/make/{KEY}', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(15000)

    # 找 Share 按钮
    share_btn = page.get_by_role('button', name=re.compile(r'Share', re.I))
    print('share buttons:', share_btn.count())
    if share_btn.count() == 0:
        # 找任何含 Share 的元素
        els = page.evaluate("""() => {
            const found = [];
            for (const el of document.querySelectorAll('button,[role=button]')) {
                const t = (el.textContent||'').trim();
                if (/share/i.test(t) && t.length < 30) found.push(t);
            }
            return found.slice(0,10);
        }""")
        print('share-like elements:', els)
        # 尝试直接点 header 里的 Share
        clicked = page.evaluate("""() => {
            const els = [...document.querySelectorAll('button,[role=button]')];
            const t = els.find(e => /^\\s*share\\s*$/i.test((e.textContent||'').trim()));
            if (t) { t.click(); return true; }
            return false;
        }""")
        print('clicked share:', clicked)
    else:
        share_btn.first.click()
        print('clicked first share button')
    page.wait_for_timeout(6000)

    # 抓弹窗内容
    body = page.evaluate("() => document.body.innerText.slice(0, 4000)")
    print('\n--- after share click ---')
    print(body[:3500])

    # 找 link access 相关控件
    acc = page.evaluate("""() => {
        const out = [];
        for (const el of document.querySelectorAll('[role=menuitem],select,option,[data-testid]')) {
            const t = (el.textContent||'').trim();
            if (/link|access|private|public|anyone|invite/i.test(t) && t.length < 60) {
                out.push((el.getAttribute('data-testid')||'')+'|'+t.slice(0,50));
            }
        }
        return [...new Set(out)].slice(0, 20);
    }""")
    print('\n--- link access controls ---')
    for x in acc:
        print(' ', x)

    # 截图保存
    try:
        page.screenshot(path='_share_modal.png')
        print('screenshot saved')
    except Exception as e:
        print('screenshot err:', str(e)[:100])
    b.close()
