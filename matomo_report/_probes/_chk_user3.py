# -*- coding: utf-8 -*-
import subprocess

cli = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64\bin\mariadb.exe'
sql = "SHOW TABLES LIKE 'matomo_user'; SELECT login, email, superuser_access FROM matomo_user;"
r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-umatomo', '-pmatomo',
                    'matomo', '-e', sql],
                   capture_output=True, text=True, timeout=30)
print('RC', r.returncode)
print(r.stdout)
print(r.stderr[-300:])
