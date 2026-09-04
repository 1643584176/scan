# -*- coding: utf-8 -*-
p = r'D:\scan\netlify_report\_net_cleanup_end.py'
t = open(p, encoding='utf-8').read()
t = t.replace('    return st, raw[:2000]', '    return st, raw')
open(p, 'w', encoding='utf-8', newline='').write(t)
print('patched, return line now:', 'return st, raw[:2000]' in t)
