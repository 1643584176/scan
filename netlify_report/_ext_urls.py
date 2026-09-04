# -*- coding: utf-8 -*-
"""扫描 extension 二进制中全部 URL 字符串,找 token 使用场景"""
import re

data = open(r'D:\scan\netlify_report\_ext_binary.bin', 'rb').read()
urls = set()
for m in re.finditer(rb'https?://[A-Za-z0-9._~:/?#@!$&()*+,;=%-]{4,200}', data):
    u = m.group(0).decode('ascii', 'ignore')
    urls.add(u)
for u in sorted(urls):
    print(u)
print('--- total', len(urls))
# 同时找 env 变量名形式的字符串(全大写+下划线,可能被 Getenv)
envs = set()
for m in re.finditer(rb'[A-Z][A-Z0-9_]{5,40}', data):
    e = m.group(0).decode('ascii')
    if 'LAMBDA' in e or 'AWS' in e or 'NETLIFY' in e or 'TOKEN' in e or 'SECRET' in e or 'KEY' in e:
        envs.add(e)
for e in sorted(envs):
    print('ENV?', e)
