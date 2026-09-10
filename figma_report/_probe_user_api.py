# -*- coding: utf-8 -*-
"""探测: A 身份读 /api/user 拿 email (自读) + 考古 file_permissions_modal 角色变更端点"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\figma_report')
from _figma_creds import COOKIE_B, UID_A
import requests, urllib3
urllib3.disable_warnings()

BASE = 'https://www.figma.com'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36',
      'Origin': 'https://www.figma.com'}
hdr = {'User-Agent': UA['User-Agent'], 'Origin': UA['Origin'], 'Cookie': COOKIE_B, 'X-Figma-User-ID': UID_A}

# 1. A 自读 user
for p in ['/api/user', '/api/me']:
    try:
        r = requests.get(BASE + p, headers=hdr, timeout=20, verify=False)
        print(f'[A GET {p}] {r.status_code} :: {r.text[:600]}')
    except Exception as e:
        print(f'[A GET {p}] ERR {e}')

# 2. 考古 main JS: 文件分享弹窗 role 变更 (active user 降级/升级)
data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()
for kw in ['user_roles', 'role_users', 'change_role', 'role_change', 'make_viewer', 'update_role',
           'permission_change', 'changePermission', 'file_role']:
    ms = list(re.finditer(re.escape(kw), data))
    if ms:
        print(f'===== [{kw}] x{len(ms)} =====')
        for m in ms[:3]:
            s = max(0, m.start() - 250)
            e = min(len(data), m.end() + 250)
            print(f'@{m.start()}: {data[s:e].replace(chr(10)," ")[:520]}')
            print()
print('ALL DONE')
