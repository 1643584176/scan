# -*- coding: utf-8 -*-
# q50: billing 族端点全集 + notification 平级端点（找同表兄弟入口）
import sys, io, os, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

files = list(dict.fromkeys(glob.glob('_js/**/*.js', recursive=True) + glob.glob('_js/*.js')))
print(f'JS 文件: {len(files)} 个')

def collect(name, pattern):
    print(f'\n### {name} —— /{pattern}/')
    found = {}
    rx = re.compile(pattern)
    for f in files:
        try:
            txt = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for m in rx.finditer(txt):
            key = m.group(0)
            found.setdefault(key, os.path.basename(f))
    for k, v in sorted(found.items()):
        print(f'  {k}   [{v}]')
    if not found:
        print('  (无命中)')

collect('billing 族路径全集', r'/api/billing/[a-z_0-9/\$\{\}\.]{0,50}')
collect('notification 相关路径', r'/api/[a-z_0-9/\$\{\}\.]*notification[a-z_0-9/\$\{\}\.]*')
collect('email/settings 相关端点', r'/api/[a-z_0-9/\$\{\}\.]*(?:email_settings|settings_v\d|user_settings)[a-z_0-9/\$\{\}\.]*')
collect('subscription/plan 端点', r'/api/[a-z_0-9/\$\{\}\.]*(?:subscription|checkout|upgrade|downgrade)[a-z_0-9/\$\{\}\.]{0,30}')
