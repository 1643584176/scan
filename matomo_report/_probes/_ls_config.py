# -*- coding: utf-8 -*-
import os
import time

d = r'F:\scan\matomo_report\_src\matomo-release\matomo\config'
for f in sorted(os.listdir(d)):
    p = os.path.join(d, f)
    st = os.stat(p)
    print(f, time.strftime('%H:%M:%S', time.localtime(st.st_mtime)), st.st_size)
