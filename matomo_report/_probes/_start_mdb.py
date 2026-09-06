# -*- coding: utf-8 -*-
"""Start mariadbd in background (port 3307) and create matomo db/user."""
import os
import subprocess
import sys
import time

BASE = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64'
DATA = r'F:\scan\matomo_report\_runtime\mariadb\data'
LOG = r'F:\scan\matomo_report\_runtime\mariadb\mariadbd.log'

exe = os.path.join(BASE, 'bin', 'mariadbd.exe')
logf = open(LOG, 'a', encoding='utf-8', errors='replace')
p = subprocess.Popen([exe, '--datadir=' + DATA, '--port=3307',
                      '--bind-address=127.0.0.1', '--console'],
                     stdout=logf, stderr=logf)
print('mariadbd pid:', p.pid)
time.sleep(8)

cli = os.path.join(BASE, 'bin', 'mariadb.exe')
for i in range(5):
    r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-uroot', '-e', 'SELECT 1'],
                       capture_output=True, text=True, timeout=30)
    if r.returncode == 0:
        print('server up after %ds' % (8 + i * 3))
        break
    time.sleep(3)
else:
    print('server FAILED to start; log tail:')
    print(open(LOG, encoding='utf-8', errors='replace').read()[-3000:])
    sys.exit(1)

sql = ("CREATE DATABASE IF NOT EXISTS matomo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
       "CREATE USER IF NOT EXISTS 'matomo'@'127.0.0.1' IDENTIFIED BY 'matomo';"
       "CREATE USER IF NOT EXISTS 'matomo'@'localhost' IDENTIFIED BY 'matomo';"
       "GRANT ALL PRIVILEGES ON matomo.* TO 'matomo'@'127.0.0.1';"
       "GRANT ALL PRIVILEGES ON matomo.* TO 'matomo'@'localhost';"
       "FLUSH PRIVILEGES;")
r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-uroot', '-e', sql],
                   capture_output=True, text=True, timeout=60)
print('create db/user exit:', r.returncode, (r.stderr or '')[-500:])
r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-umatomo', '-pmatomo',
                    '-e', 'SHOW DATABASES;'],
                   capture_output=True, text=True, timeout=30)
print('matomo user check:', r.stdout, r.stderr[-300:])
print('PID FILE NOTE: mariadbd running pid', p.pid)
