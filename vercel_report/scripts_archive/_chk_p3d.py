# -*- coding: utf-8 -*-
"""p3 里 containers/drives/usage/processes 相关字符串 (字段名线索)"""
import io, re

lines = io.open('_v105p3_local.txt', encoding='utf-8', errors='replace').read().splitlines()
kws = ['containers.', 'drives.', 'usage.', 'processes.', 'CreateRequest', 'drive', 'Drive', 'snapshot', 'Snapshot',
       'oci', 'Oci', 'image', 'Image', 'mount', 'Mount', 'network', 'Network', 'env', 'Env', 'privileged']
seen = set()
for l in lines:
    s = l[2:]
    if any(k in s for k in kws):
        key = s[:130]
        if key not in seen:
            seen.add(key)
            print(s[:160])
