# -*- coding: utf-8 -*-
"""沙箱内 python 提取 init.bin 字符串: 确认 Go 二进制 + 关键协议字符串"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import cmd

SID = "sbx_PcSQVxXAgAuH9friOUhAFMWvlmr4"

def run(script, tm=90000):
    c, r = cmd(SID, "bash", ["-c", script], timeout_ms=tm)
    print("=== %d ===" % c)
    print(r[:3000])
    print()
    return r

PY = r'''
import re, gzip
data = open('/vercel/sandbox/init.bin','rb').read()
print('size', len(data))
print('head', data[:4].hex())
# Go buildinfo?
i = data.find(b'\xff Go buildinfo:')
print('go buildinfo offset', i)
# 提取 ASCII 字符串
strs = re.findall(rb'[\x20-\x7e]{6,}', data)
def has(kw):
    return [s.decode() for s in strs if kw.encode() in s.lower()][:20]
print('--- spawn ---')
print(has('spawn'))
print('--- signature ---')
print(has('signature'))
print('--- pubkey ---')
print(has('pubkey'))
print('--- ed25519 ---')
print(has('ed25519'))
print('--- vercel.sandbox ---')
print(has('vercel.sandbox'))
print('--- connect ---')
print(has('connect'))
'''

run("python3 -c " + repr(PY), 90000)
