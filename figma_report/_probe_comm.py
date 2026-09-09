# -*- coding: utf-8 -*-
"""抓 figma.com/community 公开插件页, 提取资源 ID + 检查 SSR"""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'}
for path in ['/community/explore/plugins', '/community/explore/widgets', '/community']:
    try:
        r = requests.get('https://www.figma.com' + path, headers=UA, timeout=25, verify=False)
        print(f'== {path} -> {r.status_code} len={len(r.text)}')
        t = r.text
        # 找 plugin id 形态 (20位数字)
        ids = re.findall(r'/(?:plugin|widget)/(\d{15,25})', t)
        print(f'   resource ids: {list(dict.fromkeys(ids))[:10]}')
        # 找内嵌 JSON 中 id 字段
        m = re.findall(r'"id":"(\d{15,25})"', t)
        print(f'   json ids: {list(dict.fromkeys(m))[:10]}')
        open(f'_comm_{path.split("/")[-1] or "home"}.html', 'w', encoding='utf-8').write(t)
    except Exception as e:
        print(f'== {path} ERR {e}')
print('ALL DONE')
