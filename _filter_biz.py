# -*- coding: utf-8 -*-
"""过滤 _biz_all.txt 中与网络/认证/进程管理相关的函数"""
import re

lines = open("_biz_all.txt", encoding="utf-8", errors="replace").read().splitlines()
pat = re.compile(
    r"spawnservice|listener|accept|cred|reaper|kill|signal|unix|serve|listen|http|h2|"
    r"verifier|interceptor|auth|signature|tls|cert|verify",
    re.I,
)
for ln in lines:
    if pat.search(ln):
        print(ln)
