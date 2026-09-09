# -*- coding: utf-8 -*-
"""V41: 查残留进程 17392 命令行 + B profile associated_users 状态
1. 用 psutil (若无则 wmic) 查 PID 17392 的 cmdline
2. B upsert 读 associated_users —— A 是否仍是 B profile 关联用户
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\figma_report')
from _figma_creds import COOKIE_B, UID_A, UID_B
import requests, urllib3
urllib3.disable_warnings()
BASE = 'https://www.figma.com'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36',
      'Origin': 'https://www.figma.com'}

print('===== 1. 残留进程命令行 =====')
try:
    import psutil
    for pid in [17392]:
        try:
            p = psutil.Process(pid)
            print(f'PID {pid}: name={p.name()} start={p.create_time()}')
            print(f'  cmdline={" ".join(p.cmdline())}')
        except Exception as e:
            print(f'PID {pid}: {e}')
except ImportError:
    import subprocess
    out = subprocess.run(['wmic', 'process', 'where', 'ProcessId=17392', 'get', 'CommandLine'],
                         capture_output=True, text=True)
    print('wmic:', out.stdout, out.stderr)

print()
print('===== 2. B profile associated_users =====')
def hdr(uid=None):
    h = dict(UA)
    h['Cookie'] = COOKIE_B
    if uid:
        h['X-Figma-User-ID'] = uid
    return h

r = requests.post(BASE + '/api/profile', headers=hdr(UID_B),
                  json={'primary_user_id': UID_B, 'profile_handle': 'pccp_b2_9fmvxl'}, timeout=20, verify=False)
try:
    m = r.json()['meta']
    au = m.get('associated_users')
    print(f'status={r.status_code} desc={m.get("description")!r} primary={m.get("primary_user_id")}')
    print(f'associated_users={json.dumps(au, ensure_ascii=False)[:800]}')
    if isinstance(au, list):
        for u in au:
            if str(u.get('id')) == UID_A or str(u.get('user_id')) == UID_A:
                print(f'  >>> A 仍在关联列表: {json.dumps(u, ensure_ascii=False)[:300]}')
except Exception as e:
    print(f'status={r.status_code} :: {r.text[:300]}')
print('ALL DONE')
