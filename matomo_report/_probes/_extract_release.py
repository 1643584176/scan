# -*- coding: utf-8 -*-
"""Extract matomo-latest.zip (release, includes vendor/)."""
import os
import zipfile

src = r'F:\scan\matomo_report\_src\matomo-latest.zip'
dst = r'F:\scan\matomo_report\_src\matomo-release'
os.makedirs(dst, exist_ok=True)
with zipfile.ZipFile(src) as z:
    total = len(z.infolist())
    print('entries:', total)
    for i, info in enumerate(z.infolist()):
        z.extract(info, dst)
        if i % 3000 == 0:
            print('  %d/%d' % (i, total))
print('done')
# locate actual root (zip may nest under matomo/)
root = dst
for e in os.listdir(dst):
    if os.path.isdir(os.path.join(dst, e)) and e in ('matomo', 'piwik'):
        root = os.path.join(dst, e)
print('root:', root)
print('has vendor:', os.path.isdir(os.path.join(root, 'vendor')))
print('console:', os.path.exists(os.path.join(root, 'console')))
