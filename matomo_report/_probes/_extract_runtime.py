# -*- coding: utf-8 -*-
"""Extract PHP + MariaDB portable zips (python zipfile - gitbash safe)."""
import os
import zipfile

RT = r'F:\scan\matomo_report\_runtime'
DL = os.path.join(RT, 'downloads')

def extract(zpath, dest):
    print('extracting %s -> %s' % (zpath, dest))
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        total = len(z.infolist())
        for i, info in enumerate(z.infolist()):
            z.extract(info, dest)
            if i % 2000 == 0:
                print('  %d/%d' % (i, total))
    print('done:', zpath)

extract(os.path.join(DL, 'php-8.3.33.zip'), os.path.join(RT, 'php'))
extract(os.path.join(DL, 'mariadb-11.4.13.zip'), os.path.join(RT, 'mariadb'))
print('ALL DONE')
