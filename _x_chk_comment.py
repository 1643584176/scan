# -*- coding: utf-8 -*-
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
d = open(r'F:\scan\vercel_report\fw_vpc\H1-sandbox-custom-policy-vpc-bypass-comment-en.md', encoding='utf-8').read()
cjk = re.findall(r'[\u4e00-\u9fff]+', d)
print('CJK count:', len(cjk))
print(cjk[:10])
