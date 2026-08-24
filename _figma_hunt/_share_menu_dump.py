# -*- coding: utf-8 -*-
"""打印分享弹窗当前所有可见文本 + 菜单选项, 找到正确的 audience 选项"""
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


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': 1500, 'height': 900})
    ctx.add_cookies(cookies_for_browser(raw_cookie('ws_cookie_A_new.txt')))
    page = ctx.new_page()
    page.goto(BASE + f'/make/{KEY}', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(15000)
    page.get_by_text("Share", exact=True).first.click(timeout=8000)
    page.wait_for_timeout(5000)
    page.locator('[data-testid="file-audience-row"]').first.click(timeout=8000)
    page.wait_for_timeout(4000)

    # 收集所有 button/menuitem/option 文本
    items = page.evaluate("""() => {
        const out = [];
        for (const el of document.querySelectorAll('button,[role=menuitem],[role=option],[role=combobox],[data-testid]')) {
            const t = (el.textContent || '').trim().replace(/\\s+/g, ' ');
            if (t && t.length < 120) out.push({tag: el.tagName, role: el.getAttribute('role'),
                testid: el.getAttribute('data-testid'), text: t});
        }
        return out;
    }""")
    seen = set()
    for it in items:
        k = (it['role'], it['testid'], it['text'])
        if k not in seen:
            seen.add(k)
            print(f"[{it['tag']}] role={it['role']} testid={it['testid']} :: {it['text'][:100]}")
    print('total:', len(items))
    b.close()
