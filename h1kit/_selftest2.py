# -*- coding: utf-8 -*-
import os
import sys

os.chdir(r'F:\scan')
sys.path.insert(0, r'F:\scan')
from h1kit import net

print('exit_ip:', net.exit_ip()[:80])
# probe_proxies should run without exception (all candidates closed here)
try:
    net.probe_proxies(timeout=4)
    print('probe_proxies OK')
except Exception as e:
    print('probe_proxies FAIL:', e)
