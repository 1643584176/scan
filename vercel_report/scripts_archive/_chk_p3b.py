# -*- coding: utf-8 -*-
"""分析 p3: proto 文件名 + 23456/sandboxctrl 相关 + 完整类型名"""
import io, re

lines = io.open('_v105p3_local.txt', encoding='utf-8', errors='replace').read().splitlines()
protos = set()
ctrl = set()
types = set()
for l in lines:
    s = l[2:]
    if '.proto' in s:
        protos.add(s)
    if 'sandboxctrl' in s or 'SandboxCtrl' in s or 'sandbox_ctrl' in s:
        ctrl.add(s)
    if re.match(r'^[A-Z][A-Za-z0-9]+(Request|Response)$', s):
        types.add(s)
print('=== protos (%d) ===' % len(protos))
for s in sorted(protos):
    print(' ', s[:200])
print('=== sandboxctrl (%d) ===' % len(ctrl))
for s in sorted(ctrl):
    print(' ', s[:200])
print('=== Req/Resp types (%d) ===' % len(types))
for s in sorted(types):
    print(' ', s)
