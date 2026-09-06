# -*- coding: utf-8 -*-
"""Start PHP built-in server detached (survives shell exit)."""
import os
import subprocess

PHP = r'F:\scan\matomo_report\_runtime\php\php.exe'
ROOT = r'F:\scan\matomo_report\_src\matomo-release\matomo'
LOG = open(r'F:\scan\matomo_report\_runtime\php_server.log', 'a', encoding='utf-8', errors='replace')

flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
p = subprocess.Popen([PHP, '-S', '127.0.0.1:8080', '-t', ROOT],
                     cwd=ROOT, stdout=LOG, stderr=LOG,
                     creationflags=flags)
print('php server pid:', p.pid)
