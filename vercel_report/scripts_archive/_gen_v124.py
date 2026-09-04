# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda123_guest.py', encoding='utf-8').read()
src = src.replace('vda123', 'vda124').replace('V123C_DONE', 'V124C_DONE').replace('v123', 'v124')
io.open('skills/non-traditional-vuln-hunting/vda124_guest.py', 'w', encoding='utf-8').write(src)
print('OK')
