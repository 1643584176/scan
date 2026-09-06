# -*- coding: utf-8 -*-
"""Show mariadb-install-db usage."""
import os
import subprocess

BASE = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64'
exe = os.path.join(BASE, 'bin', 'mariadb-install-db.exe')
for args in (['--help'], ['--no-defaults', '--help']):
    r = subprocess.run([exe] + args, capture_output=True, text=True, timeout=120)
    out = (r.stdout or '') + (r.stderr or '')
    print('=== ARGS:', args, 'exit:', r.returncode)
    print(out[:3500])
