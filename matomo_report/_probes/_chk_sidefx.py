# -*- coding: utf-8 -*-
"""Check DB side effects after databaseSetup POST."""
import os
import subprocess

cli = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64\bin\mariadb.exe'
r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-umatomo', '-pmatomo',
                    '-e', "SHOW TABLES FROM matomo LIKE 'matomo_%' LIMIT 15;"
                          "SELECT COUNT(*) AS tbl_cnt FROM information_schema.tables "
                          "WHERE table_schema='matomo';"],
                   capture_output=True, text=True, timeout=30)
print('RC', r.returncode)
print(r.stdout)
print(r.stderr[-800:])

cfg = r'F:\scan\matomo_report\_src\matomo-release\matomo\config\config.ini.php'
print('config.ini.php exists:', os.path.exists(cfg))
if os.path.exists(cfg):
    print(open(cfg, encoding='utf-8', errors='replace').read()[:800])
