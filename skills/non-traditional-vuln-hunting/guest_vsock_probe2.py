# -*- coding: utf-8 -*-
"""guest_vsock_probe2: vsock host 面深入探测
1) 端口扫描扩展 (1024-1100 / 2048-2060 / 3000-3010 / 5000-5010 / 8000-8010 / 9000-9010)
2) 1026 Datadog agent: 完整 /info 全文 + /debugger/v2/input POST + 其他端点, 响应全文落盘
3) 2050 H2: 完整握手 (收 SETTINGS -> ACK -> HEADERS -> 解析帧)
4) 1025: 协议探测 (HTTP/1.1 + H2 preface)
输出落盘 + 哨兵 VSOCK2_DONE"""
import os, socket, struct, ctypes, time, signal, sys, base64

OUT = '/vercel/sandbox/vsock2.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


signal.alarm(170)

libc = ctypes.CDLL(None, use_errno=True)


def syscall(n, *args):
    libc.syscall.restype = ctypes.c_long
    return libc.syscall(n, *args)


SYS_IO_URING_SETUP = 425
SYS_IO_URING_ENTER = 426
IORING_OFF_SQ_RING = 0
IORING_OFF_SQES = 0x10000000
IORING_OP_SOCKET = 45
IORING_ENTER_GETEVENTS = 1
PROT_RW = 3
MAP_SHARED_POP = 0x8001
AF_VSOCK = 40
CID_HOST = 2


class SQRingOffsets(ctypes.Structure):
    _fields_ = [('head', ctypes.c_uint32), ('tail', ctypes.c_uint32),
                ('ring_mask', ctypes.c_uint32), ('ring_entries', ctypes.c_uint32),
                ('flags', ctypes.c_uint32), ('dropped', ctypes.c_uint32),
                ('array', ctypes.c_uint32), ('resv1', ctypes.c_uint32),
                ('user_addr', ctypes.c_uint64)]


class CQRingOffsets(ctypes.Structure):
    _fields_ = [('head', ctypes.c_uint32), ('tail', ctypes.c_uint32),
                ('ring_mask', ctypes.c_uint32), ('ring_entries', ctypes.c_uint32),
                ('overflow', ctypes.c_uint32), ('cqes', ctypes.c_uint32),
                ('resv', ctypes.c_uint64 * 3)]


class Params(ctypes.Structure):
    _fields_ = [('sq_entries', ctypes.c_uint32), ('cq_entries', ctypes.c_uint32),
                ('flags', ctypes.c_uint32), ('sq_thread_cpu', ctypes.c_uint32),
                ('sq_thread_idle', ctypes.c_uint32), ('features', ctypes.c_uint32),
                ('wq_fd', ctypes.c_uint32), ('resv', ctypes.c_uint32 * 3),
                ('sq_off', SQRingOffsets), ('cq_off', CQRingOffsets)]


def setup_uring(entries=8):
    p = Params()
    rfd = syscall(SYS_IO_URING_SETUP, entries, ctypes.byref(p))
    if rfd < 0:
        log('io_uring_setup FAIL errno=%d' % ctypes.get_errno())
        return None
    libc.mmap.restype = ctypes.c_void_p
    libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
    sq_sz = p.sq_off.array + p.sq_entries * 4
    cq_sz = p.cq_off.cqes + p.cq_entries * 16
    msz = max(sq_sz, cq_sz)
    base = libc.mmap(None, msz, PROT_RW, MAP_SHARED_POP, rfd, IORING_OFF_SQ_RING)
    if base == ctypes.c_void_p(-1).value:
        return None
    cq_base = base if (p.features & 1) else libc.mmap(None, cq_sz, PROT_RW, MAP_SHARED_POP, rfd, 0x8000000)
    sqes = libc.mmap(None, p.sq_entries * 64, PROT_RW, MAP_SHARED_POP, rfd, IORING_OFF_SQES)
    return {'fd': rfd, 'p': p, 'base': base, 'cq_base': cq_base, 'sqes': sqes}


def u32(base, off):
    return ctypes.cast(base + off, ctypes.POINTER(ctypes.c_uint32))


def submit(ur, opcode, fd=0, off=0, addr=0, ud=1):
    p = ur['p']
    tail = u32(ur['base'], p.sq_off.tail)[0]
    idx = tail & u32(ur['base'], p.sq_off.ring_mask)[0]
    sqe = ur['sqes'] + idx * 64
    ctypes.memset(sqe, 0, 64)
    ctypes.c_uint8.from_address(sqe).value = opcode
    ctypes.c_int32.from_address(sqe + 4).value = fd
    ctypes.c_uint64.from_address(sqe + 8).value = off
    ctypes.c_uint64.from_address(sqe + 16).value = addr
    ctypes.c_uint64.from_address(sqe + 32).value = ud
    u32(ur['base'], p.sq_off.array)[idx] = idx
    u32(ur['base'], p.sq_off.tail)[0] = tail + 1
    n = syscall(SYS_IO_URING_ENTER, ur['fd'], 1, 0, IORING_ENTER_GETEVENTS, 0, 0)
    if n < 0:
        return -ctypes.get_errno()
    dl = time.time() + 3
    while u32(ur['cq_base'], p.cq_off.head)[0] == u32(ur['cq_base'], p.cq_off.tail)[0] and time.time() < dl:
        time.sleep(0.005)
    if u32(ur['cq_base'], p.cq_off.head)[0] == u32(ur['cq_base'], p.cq_off.tail)[0]:
        return -999
    cqe = ur['cq_base'] + p.cq_off.cqes + (
        u32(ur['cq_base'], p.cq_off.head)[0] & u32(ur['cq_base'], p.cq_off.ring_mask)[0]) * 16
    res = ctypes.c_int32.from_address(cqe + 8).value
    u32(ur['cq_base'], p.cq_off.head)[0] += 1
    return res


ur = setup_uring()
if not ur:
    log('VSOCK2_DONE')
    f.close()
    sys.exit(0)


def vsock_connect(port, timeout=2.0):
    res = submit(ur, IORING_OP_SOCKET, fd=AF_VSOCK, off=1, addr=0)
    if res < 0:
        return None, 'socket_res=%d' % res
    try:
        s = socket.socket(family=socket.AF_VSOCK, type=socket.SOCK_STREAM, fileno=res)
        s.settimeout(timeout)
        s.connect((CID_HOST, port))
        return s, None
    except Exception as e:
        try:
            os.close(res)
        except Exception:
            pass
        return None, '%s errno=%s' % (type(e).__name__, getattr(e, 'errno', ''))


def recv_all(s, t=2.0):
    s.settimeout(t)
    data = b''
    try:
        while len(data) < 131072:
            c = s.recv(8192)
            if not c:
                break
            data += c
    except socket.timeout:
        pass
    except Exception as e:
        log('recv EXC %s' % e)
    return data


def h2_frame(t, flags, stream, payload):
    return struct.pack('>I', len(payload))[1:] + bytes([t, flags]) + struct.pack('>I', stream) + payload


def probe_h2(s, port, label):
    """完整 H2 握手: preface -> SETTINGS -> 收 server SETTINGS -> ACK -> HEADERS(GET /) -> 解析帧"""
    try:
        s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
        s.sendall(h2_frame(4, 0, 0, b''))  # SETTINGS
        time.sleep(0.5)
        data = recv_all(s, 1.0)
        log('[%s:%d] after preface+SETTINGS rcvd %dB hex=%s' % (label, port, len(data), data[:60].hex()))
        if data:
            # 回 ACK
            s.sendall(h2_frame(4, 1, 0, b''))
        hp = b'\x83\x86\x84' + b'\x41\x09localhost'
        s.sendall(h2_frame(1, 0x5, 1, hp))
        time.sleep(1.2)
        data2 = recv_all(s, 3.0)
        log('[%s:%d] after HEADERS rcvd %dB hex=%s' % (label, port, len(data2), data2[:120].hex()))
        # 解析帧
        if data2:
            off = 0
            while off + 9 <= len(data2):
                ln = int.from_bytes(data2[off:off + 3], 'big')
                typ = data2[off + 3]
                fl = data2[off + 4]
                st = int.from_bytes(data2[off + 5:off + 9], 'big')
                pay = data2[off + 9:off + 9 + ln]
                log('  frame type=%d flags=0x%x stream=%d len=%d payload=%s' % (
                    typ, fl, st, ln, pay[:80].hex()))
                if typ == 1:  # HEADERS
                    log('  HEADERS payload hex=%s' % pay.hex())
                off += 9 + ln
        return data + data2
    except Exception as e:
        log('[%s:%d] EXC %s' % (label, port, type(e).__name__))
        return b''


# ---- 1) 端口面扩展 ----
log('=== vsock 端口面扩展扫描 ===')
ports = list(range(1024, 1101)) + list(range(2048, 2061)) + list(range(3000, 3011)) + \
        list(range(5000, 5011)) + list(range(8000, 8011)) + list(range(9000, 9011))
hits = []
for port in ports:
    s, err = vsock_connect(port, timeout=0.6)
    if s:
        hits.append(port)
        log('OPEN %d' % port)
        s.close()
        time.sleep(0.1)
    else:
        time.sleep(0.02)
log('OPEN 汇总: %s' % hits)

# ---- 2) 1026 Datadog agent 全端点 ----
log('=== 1026 Datadog agent 全端点 ===')
s, err = vsock_connect(1026, timeout=3)
if s:
    reqs = [
        ('GET /info', 'GET /info HTTP/1.1\r\nHost: localhost\r\nAccept: */*\r\nConnection: close\r\n\r\n'),
        ('POST /debugger/v2/input', 'POST /debugger/v2/input HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}'),
        ('GET /', 'GET / HTTP/1.1\r\nHost: localhost\r\nAccept: */*\r\nConnection: close\r\n\r\n'),
        ('GET /agent', 'GET /agent HTTP/1.1\r\nHost: localhost\r\nAccept: */*\r\nConnection: close\r\n\r\n'),
        ('POST /v0.7/traces', 'POST /v0.7/traces HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n[]'),
        ('GET /health', 'GET /health HTTP/1.1\r\nHost: localhost\r\nAccept: */*\r\nConnection: close\r\n\r\n'),
    ]
    for name, req in reqs:
        try:
            s.sendall(req.encode())
            data = recv_all(s, 2.5)
            head = data[:200].decode('latin1', 'replace').replace('\r', '\\r').replace('\n', '\\n')
            log('== %s rcvd %dB: %s' % (name, len(data), head))
            if name == 'GET /info':
                log('--- /info FULL ---')
                log(data.decode('latin1', 'replace'))
                log('--- /info END ---')
        except Exception as e:
            log('== %s EXC %s' % (name, type(e).__name__))
        time.sleep(0.5)
    s.close()

# ---- 3) 2050 H2 ----
log('=== 2050 H2 ===')
s, err = vsock_connect(2050, timeout=3)
if s:
    probe_h2(s, 2050, 'h2')
    s.close()

# ---- 4) 1025 协议探测 ----
log('=== 1025 协议探测 ===')
s, err = vsock_connect(1025, timeout=3)
if s:
    s.sendall(b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
    d1 = recv_all(s, 2.0)
    log('1025 http1 rcvd %dB: %s' % (len(d1), d1[:200].decode('latin1', 'replace')))
    s.close()
    s, err = vsock_connect(1025, timeout=3)
    if s:
        probe_h2(s, 1025, 'p1025')
        s.close()

log('VSOCK2_DONE')
f.close()
