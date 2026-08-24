# -*- coding: utf-8 -*-
"""分享设置变更: invite_only → anyone → invite_only, 两次 Save 都抓写 API"""
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
                x in u for x in ('.png', '.css', '.js', 'sentry', 'metrics', 'statsig',
                                 'figment', 'web_logger', 'keep-alive', 'ui_capabilities',
                                 'rollout', 'sandbox', '/view')):
            try:
                bd = (request.post_data or '')[:600]
            except Exception:
                bd = '<binary>'
            captured.append({'m': request.method, 'u': u[:240], 'b': bd})

    page.on('request', on_request)
    page.goto(BASE + f'/make/{KEY}', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(15000)
    page.get_by_text("Share", exact=True).first.click(timeout=8000)
    page.wait_for_timeout(5000)
    page.locator('[data-testid="file-audience-row"]').first.click(timeout=8000)
    page.wait_for_timeout(4000)

    def choose_option(text):
        # 展开 combobox
        try:
            page.locator('[role=combobox]').first.click(timeout=3000)
            page.wait_for_timeout(1500)
        except Exception:
            pass
        # 找选项
        try:
            page.locator(f'[role=option]').filter(has_text=text).first.click(timeout=3000)
            return True
        except Exception as e:
            print('option fail:', text, str(e)[:80])
            return False

    def click_save():
        try:
            page.get_by_text("Save", exact=True).first.click(timeout=3000)
            page.wait_for_timeout(4000)
            return True
        except Exception as e:
            print('save fail:', str(e)[:80])
            return False

    print('--- 改为 Anyone ---')
    choose_option("Anyone")
    page.wait_for_timeout(1500)
    click_save()
    page.wait_for_timeout(4000)

    print('\n--- 改回 People invited ---')
    # 重新打开弹窗
    try:
        page.get_by_text("Share", exact=True).first.click(timeout=5000)
        page.wait_for_timeout(3000)
    except Exception:
        pass
    try:
        page.locator('[data-testid="file-audience-row"]').first.click(timeout=5000)
        page.wait_for_timeout(2500)
    except Exception:
        pass
    choose_option("People invited")
    page.wait_for_timeout(1500)
    click_save()
    page.wait_for_timeout(4000)

    print('\n=== WRITE API calls ===')
    for c in captured:
        print(c['m'], c['u'])
        if c['b']:
            print('   body:', c['b'])
    print('total:', len(captured))
    b.close()
