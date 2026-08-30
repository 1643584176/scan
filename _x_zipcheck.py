# -*- coding: utf-8 -*-
import zipfile, os

p = r'F:\scan\vercel_report\fw_vpc\fw_vpc_poc.zip'
z = zipfile.ZipFile(p)
total = 0
for n in z.namelist():
    print(n, z.getinfo(n).file_size)
    total += z.getinfo(n).file_size
print('FILES:', len(z.namelist()), 'TOTAL:', total)
print('SIZE:', os.path.getsize(p))
