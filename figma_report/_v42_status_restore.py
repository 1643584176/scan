# -*- coding: utf-8 -*-
"""V42: 状态判定 + 现场恢复
1. B 读全字段: associated_users 里是否有 A? desc 当前值?
2. 判定: A 已无关联 && desc=t2-probe -> A 的 PUT 生效(BOLA 证据)
3. 恢复: B 身份 PUT desc='' 并复查直到生效
"""
import sys, io, json, time
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

def read(label):
    r = requests.post(BASE + '/api/profile', headers=hdr(UID_B),
                      json={'primary_user_id': UID_B, 'profile_handle': 'pccp_b2_9fmvxl'}, timeout=20, verify=False)
    try:
        m = r.json()['meta']
        au = m.get('associated_users') or []
        au_ids = []
        for u in au:
            au_ids.append(u.get('id') if isinstance(u, dict) else u)
        print(f'[{label}] {r.status_code} desc={m.get("description")!r} primary={m.get("primary_user_id")} assoc={au_ids}')
        return m
    except Exception:
        print(f'[{label}] {r.status_code} :: {r.text[:200]}')
        return None

print('===== 1. 当前状态 =====')
m = read('B 读')
if m:
    a_in_assoc = any(str(u.get('id')) == UID_A for u in (m.get('associated_users') or []) if isinstance(u, dict))
    print(f'A in associated_users: {a_in_assoc}')
    print(f'desc == t2-probe (A 写入残留): {m.get("description") == "t2-probe"}')
    if not a_in_assoc and m.get('description') == 't2-probe':
        print('>>> 判定: A 无关联但 PUT 生效 -> PUT /api/profile/{id} 无 ACL 嫌疑成立')

print()
print('===== 2. 恢复 desc=\'\' (B 身份, 最多 3 轮) =====')
ok = False
for i in range(3):
    r = requests.put(BASE + f'/api/profile/{PID_B}', headers=hdr(UID_B),
                     json={'description': ''}, timeout=20, verify=False)
    print(f'[B 恢复-{i}] PUT -> {r.status_code}')
    time.sleep(5)
    m2 = read(f'恢复复查-{i}')
    if m2 and m2.get('description') in ('', None):
        ok = True
        print('恢复完成')
        break
print(f'恢复结果: {"OK" if ok else "未生效(需重试)"}')
print('ALL DONE')
