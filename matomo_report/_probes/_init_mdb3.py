# -*- coding: utf-8 -*-
"""Init MariaDB with mariadb-install-db -d <datadir>."""
import os
import shutil
import subprocess

BASE = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64'
DATA = r'F:\scan\matomo_report\_runtime\mariadb\data'

if os.path.isdir(DATA):
    shutil.rmtree(DATA)
os.makedirs(DATA)

exe = os.path.join(BASE, 'bin', 'mariadb-install-db.exe')
r = subprocess.run([exe, '-d', DATA], capture_output=True, text=True, timeout=900)
out = (r.stdout or '') + (r.stderr or '')
print('exit:', r.returncode)
print(out[-2500:])
files = os.listdir(DATA)
print('data files (%d): %s' % (len(files), sorted(files)[:25]))
print('has mysql dir:', os.path.isdir(os.path.join(DATA, 'mysql')))
