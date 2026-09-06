# -*- coding: utf-8 -*-
"""Start mariadbd + php server as detached services (survive console closes)."""
import os
import subprocess
import time

FLAGS = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

# --- mariadbd ---
MDB = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64'
DATA = r'F:\scan\matomo_report\_runtime\mariadb\data'
mdb_log = open(r'F:\scan\matomo_report\_runtime\mariadb\mariadbd.log', 'a',
               encoding='utf-8', errors='replace')
p1 = subprocess.Popen([os.path.join(MDB, 'bin', 'mariadbd.exe'),
                       '--datadir=' + DATA, '--port=3307',
                       '--bind-address=127.0.0.1', '--console'],
                      stdout=mdb_log, stderr=mdb_log, stdin=subprocess.DEVNULL,
                      creationflags=FLAGS)
print('mariadbd pid:', p1.pid)

cli = os.path.join(MDB, 'bin', 'mariadb.exe')
up = False
for i in range(20):
    r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-uroot', '-e', 'SELECT 1'],
                       capture_output=True, text=True, timeout=20)
    if r.returncode == 0:
        up = True
        print('mariadb up after %ds' % (i * 2))
        break
    time.sleep(2)
if not up:
    print('mariadb FAILED')
    print(open(r'F:\scan\matomo_report\_runtime\mariadb\mariadbd.log',
               encoding='utf-8', errors='replace').read()[-2500:])
    raise SystemExit(1)

# ensure db/user exist (idempotent)
sql = ("CREATE DATABASE IF NOT EXISTS matomo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
       "CREATE USER IF NOT EXISTS 'matomo'@'127.0.0.1' IDENTIFIED BY 'matomo';"
       "CREATE USER IF NOT EXISTS 'matomo'@'localhost' IDENTIFIED BY 'matomo';"
       "GRANT ALL PRIVILEGES ON matomo.* TO 'matomo'@'127.0.0.1';"
       "GRANT ALL PRIVILEGES ON matomo.* TO 'matomo'@'localhost';"
       "FLUSH PRIVILEGES;")
r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-uroot', '-e', sql],
                   capture_output=True, text=True, timeout=60)
print('db/user ensure exit:', r.returncode)

# --- php built-in server ---
PHP = r'F:\scan\matomo_report\_runtime\php\php.exe'
ROOT = r'F:\scan\matomo_report\_src\matomo-release\matomo'
php_log = open(r'F:\scan\matomo_report\_runtime\php_server.log', 'a',
               encoding='utf-8', errors='replace')
p2 = subprocess.Popen([PHP, '-S', '127.0.0.1:8080', '-t', ROOT],
                      cwd=ROOT, stdout=php_log, stderr=php_log,
                      stdin=subprocess.DEVNULL, creationflags=FLAGS)
print('php pid:', p2.pid)
time.sleep(2)
print('DONE')
