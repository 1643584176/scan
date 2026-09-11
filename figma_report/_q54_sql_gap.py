# -*- coding: utf-8 -*-
# q54: 本地核查——"纯SQL结构/传输残余" 8 组模式在历史脚本中是否已打
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = r'D:\scan\figma_report'
files = [f for f in glob.glob(os.path.join(d, '_*.py')) if '_q54' not in f]
print(f'扫描脚本数: {len(files)}')

pats = {
    'A. 路径版本 v2/v1': r'(billing/v[123]|v[123]/billing|notification_settings/v[123])',
    'B. 兄弟操作 copy/bulk/history/audit': r'(notification_settings/(copy|bulk|history|audit)|_settings/copy)',
    'C. 同表其他路径 user/settings': r'(api/user/notification_settings|api/notifications/settings|api/settings/notification)',
    'D. 负零 -0': r'plan_id=-0|plan_id.*%2D0|\'plan_id\':\s*-0',
    'E. multipart': r'multipart',
    'F. 时间戳写入 created_at': r"'created_at'|'updated_at'|\"created_at\"|\"updated_at\"",
    'G. JSON重复键': r'"plan_id":.{0,30}"plan_id":|\'plan_id\'.{0,30}\'plan_id\'',
    'H. file_key/sha1互换': r'(file_key.{0,40}sha1.*互换|sha1.*file_key.*互换)',
}
for name, p in pats.items():
    print(f'\n===== {name} =====')
    rx = re.compile(p)
    hits = 0
    for f in files:
        try:
            t = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for i, line in enumerate(t.splitlines(), 1):
            if rx.search(line):
                hits += 1
                if hits <= 8:
                    print(f'  {os.path.basename(f)}:{i}: {line.strip()[:140]}')
    print(f'  → 命中行数: {hits}')
print('\nDONE q54')
