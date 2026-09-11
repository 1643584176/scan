# -*- coding: utf-8 -*-
"""q40: notification_settings 调用链 — planId 来源与形态"""
import io, re, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:\scan\figma_report')

JS_DIR = '_js'
js_files = sorted(os.listdir(JS_DIR))

def read(p):
    try: return io.open(p, encoding='utf-8', errors='replace').read()
    except Exception: return ''

# 1) getNotificationSettings 调用点
print('### 1) getNotificationSettings 调用点')
for jf in js_files:
    js = read(os.path.join(JS_DIR, jf))
    for m in re.finditer(r'getNotificationSettings', js):
        s = max(0, m.start() - 900); e = m.end() + 700
        seg = js[s:e].replace('\n', ' ')
        print(f'--- [{jf}] @{m.start()} ...{seg}...')
        print()

# 2) planId 的赋值处(UUID or number 线索)
print('### 2) planId 赋值上下文(限 billing/plan 相关)')
cnt = 0
for jf in js_files:
    js = read(os.path.join(JS_DIR, jf))
    for m in re.finditer(r'plan[_]?[Ii]d["\']?\s*[:=]', js):
        s = max(0, m.start() - 400); e = m.end() + 400
        seg = js[s:e].replace('\n', ' ')
        if 'billing' in seg or 'plan_' in seg or 'Notification' in seg:
            print(f'--- [{jf}] ...{seg[:800]}...')
            cnt += 1
        if cnt >= 8: break
    if cnt >= 8: break
print(f'(共 {cnt} 处)')

# 3) /api/billing 全部端点
print()
print('### 3) /api/billing/ 全部端点')
eps = set()
for jf in js_files:
    js = read(os.path.join(JS_DIR, jf))
    for m in re.finditer(r'/api/billing/[a-zA-Z0-9_/\-${}]{2,80}', js):
        eps.add(m.group(0))
for e in sorted(eps): print('  ', e)
