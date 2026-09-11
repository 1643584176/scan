# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
for f in ['_q26_gap_result.json', '_q31b_result.json', '_q35_result.json', '_q34_result.json']:
    d = json.load(io.open(f, encoding='utf-8'))
    ks = []
    for k, v in d.items():
        if isinstance(v, (list, dict)): ks.append(f'{k}(len={len(v)})')
        else: ks.append(f'{k}={v}')
    print(f, '->', ', '.join(ks))
