# -*- coding: utf-8 -*-
import subprocess

cli = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64\bin\mariadb.exe'
r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-uroot', '-e',
                    "SELECT COUNT(*) c FROM information_schema.tables WHERE table_schema='matomo';"
                    "SHOW PROCESSLIST;"],
                   capture_output=True, text=True, timeout=30)
print(r.stdout)
print(r.stderr[-300:])
