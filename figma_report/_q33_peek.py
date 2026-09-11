# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
d = json.load(io.open(r'D:\scan\figma_report\_q31b_result.json', encoding='utf-8'))
tb = d['txt_but_never']
print(f'txt_but_never 总数: {len(tb)}')
print('\n=== 前 100 个 ===')
for k in tb[:100]:
    print('  ', k)
print('\n=== 随机中段样本 ===')
for k in tb[300:360]:
    print('  ', k)
