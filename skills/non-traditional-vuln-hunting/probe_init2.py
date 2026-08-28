# -*- coding: utf-8 -*-
"""沙箱内 strings 侦察 sandbox-init: Spawn 服务/protobuf/签名逻辑线索"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import cmd

SID = "sbx_PcSQVxXAgAuH9friOUhAFMWvlmr4"

def run(script, tm=60000):
    c, r = cmd(SID, "bash", ["-c", script], timeout_ms=tm)
    print("=== %d ===" % c)
    print(r[:2500])
    print()
    return r

# 1. Spawn 相关字符串
run("strings -n 6 /vercel/sandbox/init.bin 2>/dev/null | grep -iE 'Spawn(Request|Response|Service|Error)' | head -30")
# 2. 签名相关
run("strings -n 6 /vercel/sandbox/init.bin 2>/dev/null | grep -iE 'X-Signature|X-Timestamp|signature|pubkey|ed25519|verify' | head -30")
# 3. 服务路径
run("strings -n 6 /vercel/sandbox/init.bin 2>/dev/null | grep -E 'vercel.sandbox' | head -30")
# 4. protobuf 字段线索
run("strings -n 6 /vercel/sandbox/init.bin 2>/dev/null | grep -iE 'cwd|argv|env|sessionId|exitCode|stdout|stderr|spawn' | head -40")
