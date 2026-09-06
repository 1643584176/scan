# -*- coding: utf-8 -*-
import subprocess

cli = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64\bin\mariadb.exe'
sql = "SHOW TABLES LIKE 'matomo_site'; SELECT idsite, name, main_url FROM matomo_site;"
r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-umatomo', '-pmatomo',
                    'matomo', '-e', sql],
                   capture_output=True, text=True, timeout=30)
print(r.stdout)
print(r.stderr[-200:])
