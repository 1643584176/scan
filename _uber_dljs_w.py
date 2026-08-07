"""下载 www.uber.com 的 JS 资源"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests
from playwright.sync_api import sync_playwright

os.makedirs('js_w', exist_ok=True)

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()
    chunks = []
    def on_req(r):
        if '.js' in r.url and 'uber.com' in r.url:
            chunks.append(r.url)
    page.on('request', on_req)
    page.goto('https://www.uber.com/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(12000)
    scripts = page.evaluate("() => [...document.querySelectorAll('script[src]')].map(s => s.src)")
    all_urls = list(dict.fromkeys(scripts + chunks))
    print(f'JS 数量: {len(all_urls)}')
    br.close()

H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'}
saved = 0
for i, u in enumerate(all_urls):
    try:
        r = requests.get(u, headers=H, timeout=20)
        if r.status_code == 200 and len(r.text) > 100:
            name = re.sub(r'[^\w.\-]', '_', u.split('/')[-1])[:80]
            fn = f'js_w/{i:03d}_{name}'
            open(fn, 'w', encoding='utf-8', errors='replace').write(r.text)
            saved += 1
    except Exception as e:
        pass
print(f'下载成功: {saved}')
