# -*- coding: utf-8 -*-
"""Enable MariaDB general log for SQL diffing."""
import subprocess

cli = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64\bin\mariadb.exe'
sql = ("SET GLOBAL general_log = 'ON';"
       "SET GLOBAL general_log_file = 'F:/scan/matomo_report/_runtime/mariadb/matomo_general.log';"
       "SHOW VARIABLES LIKE 'general_log%';")
r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-uroot', '-e', sql],
                   capture_output=True, text=True, timeout=30)
print(r.stdout)
print(r.stderr[-300:])
