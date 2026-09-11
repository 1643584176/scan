# -*- coding: utf-8 -*-
# r210e: apply_hub 5脚本性质 + r130 claim + mark 全局复查
import os, io
d = 'D:/scan/figma_report'

print('===== apply_hub 5 脚本性质 =====')
for fn in ['_figma_r29_js_sites.py', '_figma_r38_cmstry.py', '_figma_r60_cmsctx.py',
           '_figma_r61_covercheck.py', '_figma_r69_oracle.py']:
    p = os.path.join(d, fn)
    s = io.open(p, encoding='utf-8', errors='replace').read()
    has_http = 'requests.' in s
    print('==', fn, ':: HTTP请求=', has_http)
    for i, line in enumerate(s.split('\n')):
        if 'apply_hub' in line or 'applyHub' in line:
            print('   L%d: %s' % (i + 1, line.strip()[:170]))

print()
print('===== _figma_r130.py claim 相关行 =====')
p = os.path.join(d, '_figma_r130.py')
s = io.open(p, encoding='utf-8', errors='replace').read()
print('HTTP请求=', 'requests.' in s, '总行数=', len(s.split('\n')))
for i, line in enumerate(s.split('\n')):
    low = line.lower()
    if 'claim' in low or 'mark_diagram' in low or 'markinsert' in low:
        print('   L%d: %s' % (i + 1, line.strip()[:170]))

print()
print('===== mark_diagram / markInserted 全局（排除 r210 临时脚本）=====')
for root, dirs, files in os.walk(d):
    if '_js' in root:
        continue
    for fn in files:
        if fn.endswith('.py') and 'r210' not in fn:
            try:
                s2 = io.open(os.path.join(root, fn), encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            if 'mark_diagram' in s2:
                print('   [mark_diagram]', fn)
            if 'markInserted' in s2:
                print('   [markInserted]', fn)
            if 'apply_hub_file_collections' in s2:
                print('   [apply_hub_url]', fn)
print('DONE')
