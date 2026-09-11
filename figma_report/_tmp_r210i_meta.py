# -*- coding: utf-8 -*-
# r210i: apply no-op 归因——FK2 vs RuEdaoh 文件元数据对比（editorType/CMS 能力）
import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

BASE = 'https://www.figma.com'
UID_A = '1666382703778278399'
FK2 = 'laF5guxdhRzBcWmVwfKJ4e'
OLD = 'RuEdaohBLXN48WdkzS66BY'
COOKIE_A = open('_waf_cookies_new.txt', encoding='utf-8').read().strip()
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0')

s = requests.Session()
s.headers.update({'User-Agent': UA, 'X-Figma-User-ID': UID_A, 'Origin': BASE,
                  'Referer': f'{BASE}/', 'Cookie': COOKIE_A, 'Accept': 'application/json',
                  'X-Csrf-Bypass': 'yes',
                  'X-Figma-Client-Version': '1396308eb98e74bf4f7c72c27e72fc0d1e952816'})
try: s.trust_env = False
except Exception: pass

def get(tag, fk):
    try:
        r = s.get(f'{BASE}/api/file/{fk}', timeout=60)
    except Exception as e:
        print(f'[{tag}] EXC {repr(e)[:120]}', flush=True); return
    b = r.content.decode('utf-8', 'replace')
    io.open(f'_r210i_{tag}.json', 'w', encoding='utf-8').write(b)
    print(f'[{tag}] {r.status_code} len={len(b)}', flush=True)
    for kw in ('editorType', 'editor_type', 'isCms', 'cmsEnabled', 'hasCms', 'fileType',
               'makeFile', 'isSite', 'siteId', 'workshopMode', 'figFileWorkshopMode'):
        for m in list(re.finditer(re.escape(kw), b))[:2]:
            i = m.start()
            print(f'   [{kw}] ...{b[max(0,i-80):i+130]}...'.replace(chr(10), ' '), flush=True)
    time.sleep(1.2)

print('===== FK2 (apply 目标, WS 集合空) =====')
get('fk2', FK2)
print()
print('===== RuEdaoh (WS 集合非空) =====')
get('old', OLD)
print('DONE210i')
