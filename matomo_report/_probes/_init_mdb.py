# -*- coding: utf-8 -*-
"""Init MariaDB datadir via subprocess (shell-escaping-proof)."""
import os
import subprocess
import sys

BASE = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64'
DATA = r'F:\scan\matomo_report\_runtime\mariadb\data'

if os.path.isdir(DATA):
    import shutil
    shutil.rmtree(DATA)
os.makedirs(DATA)

cmd = [os.path.join(BASE, 'bin', 'mariadb-install-db.exe'),
       '--datadir=' + DATA,
       '--basedir=' + BASE]
print('RUN:', ' '.join(cmd))
r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
print('exit:', r.returncode)
out = (r.stdout or '') + (r.stderr or '')
print(out[-3000:])
print('data dir:', os.listdir(DATA)[:15] if os.path.isdir(DATA) else 'MISSING')
