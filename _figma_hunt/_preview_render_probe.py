# -*- coding: utf-8 -*-
"""匿名加载 preview 站点——看是否渲染 A 的应用内容
流程:
 1. 匿名请求 generic_cached_preview 拿 preview URL+token (A的Weave文件)
 2. playwright 匿名打开 preview URL(浏览器环境,JS 可能处理 token 流程)
 3. 记录渲染结果与请求
"""
import io, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
GIT_URL = ("https://api.figma.com/git/make/file/2386353361958857999/public/code/"
           "7e8f327c-edcf-45e4-a11a-2a3d85c686c3.git")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"

# 1. 匿名拿 preview URL
h = {"User-Agent": UA, "Accept": "*/*", "Origin": BASE, "Referer": BASE + "/make/" + A_MAKE}
url = (f"{BASE}/api/make/{A_MAKE}/11%3A13/generic_cached_preview"
       f"?git_repo_url={urllib.parse.quote(GIT_URL, safe='')}&git_ref=main")
r = urllib.request.Request(url, headers=h)
with urllib.request.urlopen(r, timeout=25) as res:
    body = res.read().decode(errors='replace')
m = re.search(r'"url":"(https://[^"]+)"', body)
preview_url = m.group(1) if m else None
print('preview_url:', preview_url)

if not preview_url:
    raise SystemExit(1)

# 2. playwright 匿名加载 preview
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': 1400, 'height': 900})
    page = ctx.new_page()

    def on_response(response):
        if response.status >= 400:
            print(f"  [resp] {response.status} {response.request.method} {response.url[:150]}")

    page.on('response', on_response)
    try:
        page.goto(preview_url, wait_until='domcontentloaded', timeout=45000)
    except Exception as e:
        print('goto err:', str(e)[:120])
    page.wait_for_timeout(12000)
    print('=== url:', page.url)
    print('=== title:', page.title())
    body_text = page.evaluate("() => document.body.innerText.slice(0, 3000)")
    print('--- body ---')
    print(body_text[:2500])
    b.close()
