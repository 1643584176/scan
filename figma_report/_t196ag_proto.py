# -*- coding: utf-8 -*-
# r196ag(AG): JS 逆向 toAPIParameters/addRepeated 序列化协议 —— 解开 typecheck 之后的传参姿势
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = io.open('_js/figma_app-main.js', encoding='utf-8', errors='replace').read()

# af1 完整错误
b = io.open('_r196af_af1.txt', encoding='utf-8', errors='replace').read()
print('#### AF1 full:', b)
print()

for pat in ['toAPIParameters', 'addRepeated', 'toQueryParameters']:
    idxs = [m.start() for m in re.finditer(re.escape(pat), JS)]
    print(f'===== pat {pat!r}: {len(idxs)} hits')
    for i in idxs[:8]:
        seg = repr(JS[max(0, i - 300):i + 300])[:620]
        print('   >>>', seg)
    print()

# requestTypes 值域
idxs = [m.start() for m in re.finditer(re.escape('requestTypes'), JS)]
print(f'===== requestTypes: {len(idxs)} hits')
for i in idxs[:10]:
    print('   >>>', repr(JS[max(0, i - 180):i + 180])[:400])
