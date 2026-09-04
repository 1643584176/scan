# -*- coding: utf-8 -*-
import zipfile, sys
z = zipfile.ZipFile(sys.argv[1])
name = sys.argv[2] if len(sys.argv) > 2 else 'probe1.js'
print(z.read(name).decode('utf-8', 'replace')[:3000])
