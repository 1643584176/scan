# -*- coding: utf-8 -*-
# r196v 判读2: 精读 v3/v4/v7/v8 全文 + JS 挖 meteringPeriodId 类型定义
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

for f in ['_r196v_v3.json', '_r196v_v4.json', '_r196v_v7.json', '_r196v_v8.json']:
    b = io.open(f, encoding='utf-8', errors='replace').read()
    print('=' * 28, f, len(b))
    print(b[:3000])
    print()

JS = io.open('_js/figma_app-main.js', encoding='utf-8', errors='replace').read()
print('#' * 30, 'JS meteringPeriod')
for pat in ['meteringPeriodId', 'metering_period']:
    idxs = [m.start() for m in re.finditer(re.escape(pat), JS)]
    print(f'--- pat {pat!r}: {len(idxs)} hits')
    for i in idxs[:6]:
        print('   >>>', repr(JS[max(0, i - 170):i + 230])[:470])
    print()
