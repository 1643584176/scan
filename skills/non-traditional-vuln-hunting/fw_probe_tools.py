# -*- coding: utf-8 -*-
"""执行 guest 命令(复用 fw_driver 的 api/cmd)"""
import sys
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import cmd, fresh_sandbox_deny_all

SID = "sbx_6M8Yg7kJadsCnQ8GlDyTeZJa6VaY"

if __name__ == "__main__":
    code = "which python3 curl openssl node nc 2>&1; echo ---; python3 -V 2>&1; node -v 2>&1"
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=30000)
    print("code:", c)
    print(r[:2000])
