# -*- coding: utf-8 -*-
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
t = open(r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\agent-tools\4214d728\9bfdd96e.txt', encoding='utf-8', errors='replace').read()
# 找 GetWishlist 相关段落
for m in re.finditer(r'GetWishlist', t):
    i = m.start()
    seg = t[max(0,i-300):i+1200]
    # 过滤:只显示包含 steamid 或 method/version 的段落
    if 'steamid' in seg or 'Method' in seg or 'version' in seg.lower():
        print('='*70)
        print(seg.replace('\n', ' ')[:1500])
        print()
