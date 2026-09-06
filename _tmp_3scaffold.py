# -*- coding: utf-8 -*-
import os
import sys

os.chdir(r'F:\scan')
sys.path.insert(0, r'F:\scan')
from h1kit import scaffold

for h, name in [('faraday_inc', 'Faraday'), ('mergify', 'Mergify'), ('matomo', 'Matomo')]:
    out = scaffold.make_report_dir(name.lower())
    p = scaffold.make_baseline_md(h, researcher='xxbo', out_dir=out)
    print(p)
