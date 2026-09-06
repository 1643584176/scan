# -*- coding: utf-8 -*-
"""Create+run a scheduled task that starts matomo services (escapes job-tree kill)."""
import subprocess
import sys
import time

PY = r'F:\scan\.venv\Scripts\python.exe'
SCRIPT = r'F:\scan\matomo_report\_probes\_start_services.py'
TN = 'matomoLocalSvc'
TR = '{} {}'.format(PY, SCRIPT)

def run(args):
    r = subprocess.run(args, capture_output=True, text=True, timeout=60)
    return r

# delete old task if exists
run(['schtasks', '/Delete', '/TN', TN, '/F'])
time.sleep(1)
r = run(['schtasks', '/Create', '/TN', TN, '/TR', TR,
         '/SC', 'ONCE', '/ST', '23:59', '/F'])
print('create rc:', r.returncode, (r.stdout + r.stderr)[-300:])
r = run(['schtasks', '/Run', '/TN', TN])
print('run rc:', r.returncode, (r.stdout + r.stderr)[-300:])
