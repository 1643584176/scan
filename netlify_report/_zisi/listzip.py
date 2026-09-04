# -*- coding: utf-8 -*-
import zipfile, sys
z = zipfile.ZipFile(sys.argv[1])
names = z.namelist()
print('total entries:', len(names))
for n in names[:80]:
    print(n)
