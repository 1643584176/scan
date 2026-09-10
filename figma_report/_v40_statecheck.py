# -*- coding: utf-8 -*-
"""V40: 现场状态检查 (只读) —— 恢复 v39 中断后的上下文
1. 是否有残留 python 进程
2. B profile 当前状态 (desc/primary/handle/user 列表) —— 判断是否残留污染
3. A profile 是否存在残留
"""
import sys, io, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\figma_report')
from _figma_creds import COOKIE_B, UID_A, UID_B
import requests, urllib3
urllib3.disable_warnings()
BASE = 'https://www.figma.com'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36',
      'Origin': 'https://www.figma.com'}
PID_B = '1667396392225089633'

def hdr(uid=None):
    h = dict(UA)
    h['Cookie'] = COOKIE_B
    if uid:
        h['X-Figma-User-ID'] = uid
    return h

print('===== 1. 残留 python 进程 =====')
try:
    out = subprocess.run(['tasklist'], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if 'python' in line.lower():
            print(line)
except Exception as e:
    print('tasklist err:', e)

print()
print('===== 2. B profile 当前状态 =====')
r = requests.post(BASE + '/api/profile', headers=hdr(UID_B),
                  json={'primary_user_id': UID_B, 'profile_handle': 'pccp_b2_9fmvxl'}, timeout=20, verify=False)
try:
    m = r.json()['meta']
    keys = list(m.keys())
    print(f'status={r.status_code}')
    for k in ['id', 'profile_handle', 'primary_user_id', 'name', 'description', 'location', 'website']:
        print(f'  {k}={m.get(k)!r}')
    print(f'  users={m.get("users")!r}')
    print(f'  all_keys={keys}')
except Exception:
    print(f'status={r.status_code} :: {r.text[:300]}')

print()
print('===== 3. 公开页 @pccp_b2_9fmvxl 显示名 =====')
try:
    rp = requests.get(BASE + '/@pccp_b2_9fmvxl', headers={'User-Agent': UA['User-Agent']}, timeout=20, verify=False)
    # 从 HTML 找 profile name 关键字段
    import re
    txt = rp.text
    for pat in [r'"name":"([^"]{1,60})"', r'<title>([^<]*)</title>', r'og:title[^>]*content="([^"]*)"']:
        mm = re.search(pat, txt)
        if mm:
            print(f'  {pat[:30]} => {mm.group(1)[:80]}')
except Exception as e:
    print('page err:', e)
print('ALL DONE')
