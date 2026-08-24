# -*- coding: utf-8 -*-
"""A 创建新 Make 文件 → 验证默认公开性
流程:
 1. A 打开 /make/new 创建新 Make 文件
 2. 记录新 fileKey
 3. 匿名打开该文件(公开性)
 4. 不删除(保留供后续私有化测试)
"""
import io, json, re, sys, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"


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
    page.goto(BASE + '/make/new', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(25000)
    match = re.search(r'/make/([A-Za-z0-9]+)', page.url)
    if not match:
        print('FAIL no make key, url=', page.url)
        raise SystemExit(1)
    key = match.group(1)
    print('NEW_MAKE_KEY', key)
    title = page.title()
    print('title:', title)
    # 页面文本(找分享设置线索)
    body = page.evaluate("() => document.body.innerText.slice(0, 1500)")
    print('body:', body[:1300])
    b.close()

    # 匿名验证公开性
    b2 = p.chromium.launch(headless=True)
    ctx2 = b2.new_context(viewport={'width': 1400, 'height': 900})
    page2 = ctx2.new_page()
    try:
        page2.goto(BASE + f'/make/{key}', wait_until='domcontentloaded', timeout=45000)
    except Exception as e:
        print('anon goto err:', str(e)[:100])
    page2.wait_for_timeout(10000)
    body2 = page2.evaluate("() => document.body.innerText.slice(0, 800)")
    print('ANON body:', body2[:700])
    b2.close()
