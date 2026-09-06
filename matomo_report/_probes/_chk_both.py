# -*- coding: utf-8 -*-
import socket
import subprocess
import time

cli = r'F:\scan\matomo_report\_runtime\mariadb\mariadb-11.4.13-winx64\bin\mariadb.exe'
r = subprocess.run([cli, '-h127.0.0.1', '-P3307', '-uroot', '-e', 'SELECT 1'],
                   capture_output=True, text=True, timeout=15)
print('mariadb rc:', r.returncode)

s = socket.create_connection(('127.0.0.1', 8080), timeout=5)
print('php 8080 open')
s.close()
