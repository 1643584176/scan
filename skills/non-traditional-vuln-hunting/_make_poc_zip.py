# -*- coding: utf-8 -*-
"""打包 fw_vpc PoC zip（不含 token/凭据文件）"""
import zipfile, os

p = r'F:\scan\vercel_report\fw_vpc\fw_vpc_poc.zip'
z = zipfile.ZipFile(p, 'w', zipfile.ZIP_DEFLATED)
src = r'F:\scan\vercel_report\fw_vpc'
guest = r'F:\scan\skills\non-traditional-vuln-hunting'
for f in os.listdir(src):
    if f.endswith('.txt'):
        z.write(os.path.join(src, f), 'evidence/' + f)
for g in ['fw_mini_guest.py', 'fw_vpc_deep_guest.py', 'fw_mini_switch_driver.py']:
    z.write(os.path.join(guest, g), 'scripts/' + g)
z.close()
print('zip size:', os.path.getsize(p))
with zipfile.ZipFile(p) as zz:
    for n in zz.namelist():
        print(' -', n)
