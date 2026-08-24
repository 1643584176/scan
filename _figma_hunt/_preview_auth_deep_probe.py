# -*- coding: utf-8 -*-
"""preview 站点加载过程深挖——抓全部请求/响应
问题: 匿名加载后 body 空。看 JS 如何认证、渲染什么、哪些请求失败
"""
import io, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
GIT_URL = ("https://api.figma.com/git/make/file/2386353361958857999/public/code/"
           "7e8f327c-edcf-45e4-a11a-2a3d85c686c3.git")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"

h = {"User-Agent": UA, "Accept": "*/*", "Origin": BASE, "Referer": BASE + "/make/" + A_MAKE}
url = (f"{BASE}/api/make/{A_MAKE}/11%3A13/generic_cached_preview"
       f"?git_repo_url={urllib.parse.quote(GIT_URL, safe='')}&git_ref=main")
r = urllib.request.Request(url, headers=h)
with urllib.request.urlopen(r, timeout=25) as res:
    body = res.read().decode(errors='replace')
m = re.search(r'"url":"(https://[^"]+)"', body)
preview_url = m.group(1)
print('preview_url:', preview_url)

log = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': 1400, 'height': 900})
    page = ctx.new_page()

    def on_response(response):
        try:
            t = response.text()[:300]
        except Exception:
            t = ''
        log.append({'status': response.status, 'method': response.request.method,
                    'url': response.url[:200], 'ct': response.headers.get('content-type', '')[:40],
                    'body': t})

    page.on('response', on_response)
    try:
        page.goto(preview_url, wait_until='domcontentloaded', timeout=45000)
    except Exception as e:
        print('goto err:', str(e)[:120])
    page.wait_for_timeout(15000)

    print('\n=== 请求日志 ===')
    for item in log:
        print(f"{item['status']} {item['method']} {item['url']} [{item['ct']}]")
        if item['body'] and ('app' in item['url'] or 'index' in item['url'] or 'main' in item['url']):
            print(f"   ↳ {item['body'][:500]}")

    print('\n=== localStorage/cookies ===')
    try:
        ls = page.evaluate("() => JSON.stringify(localStorage)")
        print('localStorage:', ls[:600])
        cookies = ctx.cookies()
        print('cookies:', [(c['name'], c['value'][:40]) for c in cookies])
    except Exception as e:
        print('evaluate err:', str(e)[:100])
    b.close()
