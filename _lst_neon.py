# -*- coding: utf-8 -*-
"""List neon_report markdown reports and recent files"""
import os
import time

base = r"F:\scan\neon_report"
for f in sorted(os.listdir(base)):
    full = os.path.join(base, f)
    if os.path.isfile(full):
        mtime = time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(full)))
        size = os.path.getsize(full)
        print("%s %8d %s" % (mtime, size, f))
