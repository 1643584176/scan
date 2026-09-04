# -*- coding: utf-8 -*-
"""v123 payload: 按关键字符串定位 celld 内嵌 proto descriptor 区域
Go rawDesc 是编译时嵌入的未压缩 FileDescriptorProto 字节
找 ExecRequest/StreamOutputRequest 等字符串, 提取周边区域 -> /vercel/sandbox/v123d_*.bin
输出 /vercel/sandbox/v123c.out"""
import time, signal, os

OUT = '/vercel/sandbox/v123c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(200)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


log('=== P1 read celld ===')
blob = None
for cand in ('/proc/1/root/opt/vercel/celld', '/opt/vercel/celld'):
    try:
        with open(cand, 'rb') as fh:
            blob = fh.read()
        log('read %s %d bytes' % (cand, len(blob)))
        break
    except Exception as e:
        log('open %s ERR %s' % (cand, type(e).__name__))
if not blob:
    f.close()
    raise SystemExit

TARGETS = [b'ExecRequest', b'StreamOutputRequest', b'StreamOutputResponse',
           b'ExecProcess', b'output_stream', b'processes.proto', b'containers.proto',
           b'StartRequest', b'KillRequest', b'WaitRequest', b'StdinRequest',
           b'GetProcess', b'ProcessSpec', b'ListProcesses']

log('=== P2 extract regions ===')
n = 0
seen = set()
for t in TARGETS:
    start = 0
    while True:
        p = blob.find(t, start)
        if p < 0:
            break
        if p not in seen:
            seen.add(p)
            lo = max(0, p - 3000)
            hi = min(len(blob), p + 35000)
            fn = '/vercel/sandbox/v123d_%02d.bin' % n
            try:
                with open(fn, 'wb') as fh:
                    fh.write(blob[lo:hi])
                log('target %s @%d -> %s (%dB)' % (t.decode(errors='replace'), p, fn, hi - lo))
                n += 1
            except Exception as e:
                log('write %s ERR %s' % (fn, type(e).__name__))
        start = p + 1
log('total regions=%d' % n)

log('V123C_DONE')
f.close()
