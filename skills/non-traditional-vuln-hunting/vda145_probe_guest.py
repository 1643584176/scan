# -*- coding: utf-8 -*-
"""v145 payload: 精确对比 v128 成功请求 vs v143/144 失败请求
打印完整请求/响应字节, 定位 400 原因
输出 /vercel/sandbox/v145c.out"""
import socket, struct, time, json, os, signal

OUT = '/vercel/sandbox/v145c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(200)

CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PROC = '/vercel.hive.cell.api.processes.v1.ProcessService'
USAGE = '/vercel.hive.cell.api.usage.v1.UsageService'
CELLS = '/vercel.hive.api.cells.v1.CellsService'
CELD = '/vercel.hive.celld.api.v1.CelldService'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def raw_req(sockpath, path, body, t=5.0, ctype='application/json', close_hdr=True):
    """发原始请求, 返回 (status, 完整响应字节)"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        if close_hdr:
            req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
                   'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
                   % (path, ctype, len(body))).encode() + body
        else:
            req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
                   'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\n\r\n'
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
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return status, d
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


# 1: 环境确认
log('=== 1 env ===')
try:
    st = os.stat(CELL)
    log('stat %s mode=%o' % (CELL, st.st_mode))
except Exception as e:
    log('stat EXC %s' % e)
try:
    log('ls /run/cell: %s' % os.listdir('/run/cell'))
except Exception as e:
    log('ls EXC %s' % e)
try:
    log('pid1: %r' % open('/proc/1/cmdline', 'rb').read(200))
except Exception as e:
    log('pid1 EXC %s' % e)

# 2: 精确复刻 v128 请求
log('=== 2 v128 replica ===')
# v128 Create: {"image": IMG}
st, d = raw_req(CELL, '%s/Create' % CTRS, json.dumps({'image': IMG}).encode(), t=8)
log('A Create(body=image) -> %s FULL=%r' % (st, d[:600]))
# v128 GetResourceUsage: {} (摘要记录 200)
st, d = raw_req(CELL, '%s/GetResourceUsage' % USAGE, b'{}', t=5)
log('B Usage/GetResourceUsage({}) -> %s FULL=%r' % (st, d[:600]))
# v128 Mount: {} (摘要记录 200)
st, d = raw_req(CELL, '%s/Mount' % CTRS, b'{}', t=5)
log('C Mount({}) -> %s FULL=%r' % (st, d[:600]))
# v128 List: {} (摘要记录 404)
st, d = raw_req(CELL, '%s/List' % CTRS, b'{}', t=5)
log('D List({}) -> %s FULL=%r' % (st, d[:600]))

# 3: v143/144 复刻 (不同 body/header)
log('=== 3 v144 replica ===')
st, d = raw_req(CELL, '%s/GetResourceUsage' % USAGE, b'{}', t=5, close_hdr=False)
log('E Usage/GetResourceUsage no-close -> %s FULL=%r' % (st, d[:600]))
st, d = raw_req(CELL, '%s/GetCellAddress' % CELLS, b'{}', t=5)
log('F Cells/GetCellAddress({}) -> %s FULL=%r' % (st, d[:600]))
st, d = raw_req(CELL, '%s/GetDriveStorageUsage' % CELD, b'{}', t=5)
log('G Celld/GetDriveStorageUsage({}) -> %s FULL=%r' % (st, d[:600]))
st, d = raw_req(CELL, '%s/Create' % CTRS, b'{}', t=5)
log('H Create({}) -> %s FULL=%r' % (st, d[:600]))

# 4: 不同 Content-Type
log('=== 4 ct variants ===')
for ct in ['application/json', 'application/connect+json', 'application/connect+proto', 'text/plain', 'application/octet-stream']:
    st, d = raw_req(CELL, '%s/GetResourceUsage' % USAGE, b'{}', t=4, ctype=ct)
    log('CT %-28s -> %s %r' % (ct, st, d[:200]))
# proto body 变体
for body in [b'', b'\x00', b'\n\x00']:
    st, d = raw_req(CELL, '%s/GetResourceUsage' % USAGE, body, t=4, ctype='application/connect+proto')
    log('PROTO %r -> %s %r' % (body, st, d[:200]))

# 5: GET 方法
log('=== 5 GET ===')
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(4)
    s.connect(CELL)
    s.sendall(b'GET /vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage HTTP/1.1\r\nHost: unix\r\nConnection: close\r\n\r\n')
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
    log('GET -> %r' % d[:400])
except Exception as e:
    log('GET EXC %s' % e)

log('V145_DONE')
f.close()
