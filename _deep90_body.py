# -*- coding: utf-8 -*-
"""提取 deep90 输出中的 login.php body / robots.txt / cert"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\out\deep33090_guest_20260829_134434.txt', 'rb').read().decode('utf-8', errors='replace')

# 找到所有 [ts] 行并还原转义
data2 = data.replace('\\n', '\n').replace('\\r', '')
lines = data2.splitlines()

for i, ln in enumerate(lines):
    if 'login.php ->' in ln or 'robots.txt ->' in ln or 'cert ' in ln or 'https ' in ln:
        print('==== line %d ====' % i)
        print(ln[:3000])
        # 打印后续 BODY 行
        for j in range(i + 1, min(i + 12, len(lines))):
            if not lines[j].startswith('[') and lines[j].strip():
                print('  >>', lines[j][:2000])
            else:
                break
        print()
