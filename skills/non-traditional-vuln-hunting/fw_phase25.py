# -*- coding: utf-8 -*-
"""Phase25: vsock host 探测 + init.sock API + image-id + capEff 补测"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_aCiW8kdYJwYLOY6KpXlqUrUqNEfq"  # fwtest11

GUEST = r'''
import os, socket, subprocess, glob

# 1) capabilities (修复 list->str)
try:
    st = open('/proc/self/status').read()
    print('[cap]', [l for l in st.splitlines() if l.startswith('Cap')], flush=True)
except Exception as e:
    print('[cap-err]', e, flush=True)

# 2) image-id / 相关标识文件
for p in ['/etc/image-id', '/etc/hostname', '/proc/1/cgroup', '/proc/self/cgroup']:
    try:
        print('[%s] %s' % (p, open(p).read()[:300].replace(chr(10), '|')), flush=True)
    except Exception as e:
        print('[%s] ERR %s' % (p, e), flush=True)

# 3) vsock 探测 (host cid=2, 常见端口; 以及 cid=0/1/3)
def vsock_probe(cid, port, timeout=2):
    try:
        s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((cid, port))
        print('[vsock %d:%d] CONNECT OK' % (cid, port), flush=True)
        try:
            s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\n\r\n')
            r = s.recv(200)
            print('[vsock %d:%d] resp %r' % (cid, port, r[:100]), flush=True)
        except Exception as e:
            print('[vsock %d:%d] send/recv EXC %s' % (cid, port, e), flush=True)
        s.close()
    except Exception as e:
        print('[vsock %d:%d] EXC %s' % (cid, port, e), flush=True)

for cid in [2, 3, 1]:
    for port in [0, 53, 80, 443, 2345, 3000, 8000, 8080, 9000, 9090, 10000, 50000, 65535]:
        vsock_probe(cid, port)

# 4) init.sock unix socket 探测
paths = ['/run/vercel/share/init.sock', '/run/vercel/share/', '/run/vercel/']
for p in paths:
    try:
        print('[ls] %s -> %s' % (p, os.listdir(p)), flush=True)
    except Exception as e:
        print('[ls] %s ERR %s' % (p, e), flush=True)
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect('/run/vercel/share/init.sock')
    print('[init.sock] CONNECT OK', flush=True)
    s.sendall(b'help\n')
    try:
        r = s.recv(300)
        print('[init.sock] resp %r' % r[:200], flush=True)
    except Exception as e:
        print('[init.sock] recv EXC %s' % (e), flush=True)
    s.close()
except Exception as e:
    print('[init.sock] EXC %s' % (e), flush=True)

# 5) sandbox-init 进程的 fd/exe 观察
try:
    print('[init-exe]', os.readlink('/proc/1/exe'), flush=True)
    print('[init-cwd]', os.readlink('/proc/1/cwd'), flush=True)
    print('[init-fds]', os.listdir('/proc/1/fd'), flush=True)
    print('[init-socklinks]', [os.readlink('/proc/1/fd/%s' % f) for f in os.listdir('/proc/1/fd')], flush=True)
except Exception as e:
    print('[init] ERR %s' % e, flush=True)

# 6) /vercel 目录结构 (bin/runtimes/sandbox)
for p in ['/vercel/bin', '/vercel/runtimes', '/vercel/sandbox']:
    try:
        print('[ls %s] %s' % (p, os.listdir(p)[:50]), flush=True)
    except Exception as e:
        print('[ls %s] ERR %s' % (p, e), flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg33.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg33.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:9000], flush=True)
