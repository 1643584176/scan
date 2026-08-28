# -*- coding: utf-8 -*-
"""探测 sandbox-init 二进制: 路径可见性/大小/类型/字符串
在现有 sandbox 上执行, 不重建"""
import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, cmd

SID = "sbx_PcSQVxXAgAuH9friOUhAFMWvlmr4"  # run12 sandbox(guest 已退出, 仍运行)

def run(command, args, tm=30000):
    c, r = cmd(SID, command, args, timeout_ms=tm)
    print("=== %s %s -> %d" % (command, ' '.join(args)[:80], c))
    print(r[:1200])
    print()
    return c, r

run("ls", ["-la", "/run/vercel/share/"])
run("bash", ["-c", "ls -la /run/vercel/share/ 2>&1; echo ---; ls -la /run/vercel/ 2>&1"])
run("bash", ["-c", "cp /run/vercel/share/sandbox-init /vercel/sandbox/init.bin 2>&1; ls -la /vercel/sandbox/init.bin 2>&1"])
run("bash", ["-c", "head -c 16 /vercel/sandbox/init.bin | xxd 2>/dev/null || head -c 16 /vercel/sandbox/init.bin | od -A x -t x1z"])
