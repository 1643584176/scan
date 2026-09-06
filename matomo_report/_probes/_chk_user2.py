# -*- coding: utf-8 -*-
import subprocess

cli = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64\bin\mariadb.exe'
r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-umatomo', '-pmatomo', 'matomo', '-e',
                    "SHOW TABLES LIKE 'matomo_user'; SELECT login, email, superuser_access FROM matomo_user;"],
                   capture_output=True, text=True, timeout=30)
print(r.stdout)
print(r.stderr[-300:])
