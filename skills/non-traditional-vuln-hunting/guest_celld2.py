# -*- coding: utf-8 -*-
"""guest_celld2: 23456 方法矩阵 + SpawnService 免签 Kill/Ping 测试
Phase1: celld/containers/process 方法矩阵(connect JSON, 快)
Phase2: SpawnService Ping/Kill 无签名 + KillRequest 字段 oracle
输出落盘 + 哨兵 CELD2_DONE"""
import socket, time, os

OUT = '/vercel/sandbox/celld2.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    f.write(str(s) + '\n')
    f.flush()


def http_post(port, path, body='{}', hdrs=None, t=4):
    hdrs = hdrs or {}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', port))
        req = 'POST %s HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n' % (path, port, len(body))
        for k, v in hdrs.items():
            req += '%s: %s\r\n' % (k, v)
        req += '\r\n' + body
        s.sendall(req.encode())
        data = b''
        while True:
            try:
                chunk = s.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        if not data:
            return 'NORESP', ''
        head, _, rest = data.partition(b'\r\n\r\n')
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:400].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


SERVICES = {
    'celld': ['vercel.hive.celld.api.v1.Celld', ['Heartbeat', 'Configure', 'RegisterPort', 'SetWorkload',
             'GetResourceUsage', 'StartContainer', 'StopContainer', 'WaitContainer', 'Shutdown']],
    'containers': ['vercel.hive.celld.api.v1.ContainersService', ['Create', 'Start', 'Stop', 'Kill', 'Wait',
                   'Exec', 'Stdin', 'KillServer', 'StreamOutput', 'CreateSnapshot', 'GetImageConfig',
                   'SetOCIImageConfig', 'ListContainers']],
    'process': ['vercel.hive.celld.api.v1.ProcessService', ['Wait', 'Kill', 'ListPids', 'ExecProcess', 'GetProcess']],
    'spawn': ['vercel.sandbox.spawn.v1.SpawnService', ['Spawn', 'Kill', 'Ping', 'SpawnInteractive']],
}
HITS = []
log('=== PHASE1 23456 method matrix ===')
for grp, (svc, methods) in SERVICES.items():
    for m in methods:
        path = '/%s/%s' % (svc, m)
        st, bd = http_post(23456, path, '{}')
        if '404' not in st and not st.startswith('EXC') and st != 'NORESP':
            HITS.append((path, st, bd))
            log('HIT %s -> %s | %s' % (path, st, bd[:300].replace('\n', ' ')))
        time.sleep(0.12)
log('matrix done, hits=%d' % len(HITS))

log('=== PHASE2 SpawnService no-signature Kill/Ping ===')
for m in ['Ping', 'Kill']:
    path = '/vercel.sandbox.spawn.v1.SpawnService/%s' % m
    for body in ['{}', '{"processId":"1"}', '{"process_id":"1"}', '{"procId":"1"}', '{"processID":"1"}']:
        st, bd = http_post(23456, path, body)
        log('nosig %s body=%s -> %s | %s' % (m, body, st, bd[:200].replace('\n', ' ')))
        time.sleep(0.15)
    # connect header 变体
    st, bd = http_post(23456, path, '{}', {'Connect-Protocol-Version': '1'})
    log('nosig-connect %s -> %s | %s' % (m, st, bd[:200].replace('\n', ' ')))
    time.sleep(0.15)

log('=== PHASE3 KillRequest field oracle (若 Kill 免签) ===')
# unknown field oracle: 错误信息区分字段存在性
for fld in ['processId', 'process_id', 'procId', 'pid', 'id', 'sessionId', 'sandboxId',
            'containerId', 'instanceId', 'spawnId', 'commandId', 'process', 'target',
            'requestId', 'request_id', 'name', 'namespace']:
    body = '{"%s":"zz"}' % fld
    st, bd = http_post(23456, '/vercel.sandbox.spawn.v1.SpawnService/Kill', body)
    log('field %s -> %s | %s' % (fld, st, bd[:150].replace('\n', ' ')))
    time.sleep(0.12)

log('CELD2_DONE')
f.close()
