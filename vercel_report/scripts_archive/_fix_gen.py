# -*- coding: utf-8 -*-
p = r'D:\scan\_gen_v58.py'
s = open(p, encoding='utf-8').read()
s = s.replace("python3 /mnt/root/v53_payload.py; sleep 99999\"],'''", "python3 /mnt/root/v58_payload.py; sleep 99999\"],'''")
s = s.replace("open('/mnt/root/v53c.out', 'a', encoding='utf-8', errors='replace').write(line + '\\\\n')",
              "open('/mnt/root/v58c.out', 'a', encoding='utf-8', errors='replace').write(line + '\\\\n')")
open(p, 'w', encoding='utf-8').write(s)
print('gen fixed')
