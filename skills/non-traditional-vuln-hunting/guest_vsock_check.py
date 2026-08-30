# -*- coding: utf-8 -*-
"""guest_vsock_check: 沙箱内 vsock 环境侦察
1) 工具链 (gcc/go/rustc/python3/node)
2) /proc/net/vsock 内容
3) /dev/vsock 存在性 + 权限
4) seccomp 拦截验证 (socket(AF_VSOCK) 直连)
5) io_uring 可用性
输出落盘 + 哨兵 VSOCK_CHECK_DONE"""
import os, socket, struct, ctypes, subprocess, time

OUT = '/vercel/sandbox/vsock_check.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    f.write(str(s) + '\n')
    f.flush()


log('=== 1) 工具链 ===')
for tool in ['gcc', 'cc', 'go', 'rustc', 'clang', 'python3', 'node', 'curl', 'ncat', 'nc']:
    try:
        r = subprocess.run(['which', tool], capture_output=True, text=True, timeout=5)
        log('%s: %s' % (tool, r.stdout.strip() or 'NO'))
    except Exception as e:
        log('%s: EXC %s' % (tool, type(e).__name__))

log('=== 2) /proc/net/vsock ===')
try:
    log(open('/proc/net/vsock').read()[:1500])
except Exception as e:
    log('ERR %s' % e)

log('=== 3) /dev/vsock ===')
try:
    st = os.stat('/dev/vsock')
    log('exists mode=%o' % (st.st_mode & 0o777))
except Exception as e:
    log('ERR %s' % e)

log('=== 4) AF_VSOCK 直连测试 ===')
try:
    s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    log('AF_VSOCK socket() OK fd=%d' % s.fileno())
    s.close()
except Exception as e:
    log('AF_VSOCK EXC %s' % type(e).__name__)

log('=== 5) io_uring 可用性 ===')
libc = ctypes.CDLL(None, use_errno=True)
try:
    # io_uring_setup(entries, params)
    class Params(ctypes.Structure):
        _fields_ = [('sq_entries', ctypes.c_uint32), ('cq_entries', ctypes.c_uint32),
                    ('flags', ctypes.c_uint32), ('sq_thread_cpu', ctypes.c_uint32),
                    ('sq_thread_idle', ctypes.c_uint32), ('features', ctypes.c_uint32),
                    ('wq_fd', ctypes.c_uint32), ('resv', ctypes.c_uint32 * 3),
                    ('sq_off', ctypes.c_uint32 * 12), ('cq_off', ctypes.c_uint32 * 11)]
    p = Params()
    SYS_IO_URING_SETUP = 425
    r = libc.syscall(SYS_IO_URING_SETUP, 8, ctypes.byref(p))
    log('io_uring_setup rc=%d errno=%d' % (r, ctypes.get_errno()))
    if r >= 0:
        log('  sq_entries=%d cq_entries=%d features=0x%x' % (p.sq_entries, p.cq_entries, p.features))
        # cq_off 布局 (Vercel 定制检查)
        log('  cq_off: %s' % list(p.cq_off))
        os.close(r)
except Exception as e:
    log('io_uring EXC %s' % type(e).__name__)

log('VSOCK_CHECK_DONE')
f.close()
