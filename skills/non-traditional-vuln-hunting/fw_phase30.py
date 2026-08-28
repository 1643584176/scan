# -*- coding: utf-8 -*-
"""Phase30: /run 下 unix socket 探测 - containerd/cell/metrics/apm"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_9efDIoJf3GAsZlyPJy9MQm6k9MMO"  # fwtest13

GUEST = r'''
import os, socket, time

# 1) /run 全目录侦察
for d in os.listdir('/run'):
    p = '/run/' + d
    try:
        if os.path.isdir(p):
            print('[ls %s] %s' % (p, os.listdir(p)[:40]), flush=True)
        else:
            print('[file %s] %s' % (p, os.path.getsize(p)), flush=True)
    except Exception as e:
        print('[ls %s] ERR %s' % (p, e), flush=True)

# mountinfo 中相关来源
for l in open('/proc/self/mountinfo'):
    if any(x in l for x in ['containerd', 'cell', 'metrics', 'apm', 'run']):
        print('[mount] %s' % l.strip(), flush=True)

# 2) 逐个 socket 探测
socks = ['/run/cell/cell.sock', '/run/metrics/metrics.sock', '/run/apm/apm.sock',
         '/run/containerd/containerd.sock', '/run/containerd/containerd.sock.ttrpc',
         '/run/containerd/s/14bb0f1fb467cd1191140fc800756c6427eb38927339122f8bd3664d2f6aa1ce',
         '/run/vercel/share/init.sock']

def probe(path, data, label):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect(path)
        s.sendall(data)
        try:
            r = s.recv(800)
            print('[%s %s] resp %r' % (label, path, r[:300]), flush=True)
        except socket.timeout:
            print('[%s %s] TIMEOUT' % (label, path), flush=True)
        except Exception as e:
            print('[%s %s] recv EXC %s' % (label, path, e), flush=True)
        s.close()
    except Exception as e:
        print('[%s %s] CONN EXC %s' % (label, path, e), flush=True)

for p in socks:
    probe(p, b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n', 'HTTP')
    probe(p, b'\x00', 'B0')
    probe(p, b'{"id":"x"}\n', 'JSON')
print('done', flush=True)
'''
code = "cat > /tmp/pg38.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg38.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:12000], flush=True)
