"""Uber 浏览器侦察：确认反爬是否挡浏览器，抓 JS 资源"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900},
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()

    targets = ['https://www.uber.com/', 'https://m.uber.com/', 'https://www.uber.com/us/en/ride/']
    for t in targets:
        try:
            page.goto(t, timeout=45000, wait_until='domcontentloaded')
            page.wait_for_timeout(5000)
            title = page.title()[:80]
            js_count = len(page.evaluate("() => [...document.querySelectorAll('script[src]')].map(s => s.src)"))
            print(f'{t}')
            print(f'  final={page.url[:90]} title={title} js={js_count}')
        except Exception as e:
            print(f'{t} ERR {str(e)[:80]}')
    br.close()
