# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
raw = open(r'F:\scan\skills\out\stringsb_strings_init_guest_20260829_131138.txt', 'rb').read().decode('utf-8', 'replace')
print('LEN:', len(raw))
print(raw[:2000])
