# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda122_guest.py', encoding='utf-8').read()
src = src.replace('vda122', 'vda123').replace('V122C_DONE', 'V123C_DONE').replace('v122', 'v123')
io.open('skills/non-traditional-vuln-hunting/vda123_guest.py', 'w', encoding='utf-8').write(src)
print('OK')
