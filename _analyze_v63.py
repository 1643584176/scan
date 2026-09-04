# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout.reconfigure(encoding='utf-8')
p = r'D:\scan\skills\out\vda63_race_guest_20260831_113407.txt'
s = io.open(p, encoding='utf-8', errors='replace').read()
# 提取 v63c.out 部分 (===COW=== 之后)
m = re.search(r'===COW===\n(.*?)(?:===SHARE===|$)', s, re.S)
body = m.group(1) if m else s
print('TOTAL chars:', len(body))
lines = body.splitlines()
print('TOTAL lines:', len(lines))
# 关键行
for kw in ['HOSTFETCH', 'FREE', 'IMDS', 'snap#60', 'snap#61', 'snap#59', 'V63C_DONE', 'V63_END', 'CHROOT_RC']:
    hits = [ln for ln in lines if kw in ln]
    print('--- %s: %d hits' % (kw, len(hits)))
    for ln in hits[:6]:
        print('   ', ln[:300])
print()
print('=== LAST 40 lines ===')
for ln in lines[-40:]:
    print(ln[:300])
