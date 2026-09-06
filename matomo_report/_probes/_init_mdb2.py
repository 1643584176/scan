# -*- coding: utf-8 -*-
"""Init MariaDB datadir with mariadbd --initialize-insecure (clean run)."""
import os
import shutil
import subprocess

BASE = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64'
DATA = r'F:\scan\matomo_report\_runtime\mariadb\data'

if os.path.isdir(DATA):
    shutil.rmtree(DATA)
os.makedirs(DATA)

cmd = [os.path.join(BASE, 'bin', 'mariadbd.exe'),
       '--initialize-insecure',
       '--datadir=' + DATA,
       '--basedir=' + BASE]
print('RUN:', ' '.join(cmd))
r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
print('exit:', r.returncode)
out = (r.stdout or '') + (r.stderr or '')
print(out[-4000:])
files = os.listdir(DATA) if os.path.isdir(DATA) else []
print('data files (%d): %s' % (len(files), files[:20]))
ok_markers = ['mysql', 'performance_schema', 'sys']
print('system dirs present:', [f for f in files if f in ok_markers])
