# -*- coding: utf-8 -*-
"""本地: 找 SpawnRequest 所有字段的 protobuf tag"""
import re

d = open("_sandbox_init_new.bin", "rb").read()

# protobuf tag 模式: protobuf:"<type>,<num>,name=<name>,json=<jsonName>,proto3"
pat = re.compile(rb'protobuf:"[^"]{0,80}name=[a-z_]+,[^"]{0,60}proto3"')
seen = set()
for m in pat.finditer(d):
    tag = m.group().decode("latin1")
    if tag not in seen:
        seen.add(tag)
        print(tag)

# 也搜 json name 候选: json=<camel>
pat2 = re.compile(rb'json=[a-zA-Z0-9_]+')
cands = set()
for m in pat2.finditer(d):
    s = m.group().decode()
    if any(k in s.lower() for k in ("command", "argv", "env", "work", "pid", "time", "pty", "shell", "snapshot", "sig", "kill")):
        cands.add(s)
for c in sorted(cands):
    print("JSON:", c)
