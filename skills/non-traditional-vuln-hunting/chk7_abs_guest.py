# -*- coding: utf-8 -*-
"""chk7_abs: CHECK 7 抽象 unix socket 枚举 + 连接探测 (J524 遗留)
1) 全量 dump /proc/net/unix (含文件系统路径与抽象 socket)
2) 对抽象 socket (@ 开头) 逐个 connect 探测, 成功则发 HTTP 探测
3) 附带: 枚举所有可写目录下新建 unix socket 的可见性 (对照)
输出落盘 + 哨兵 CHK7_DONE"""
import os, time, socket, struct

OUT = '/vercel/sandbox/chk7.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def parse_unix_table():
    """解析 /proc/net/unix, 返回 [(num, ref, flags, type, st, inode, path)]"""
    rows = []
    try:
        with open('/proc/net/unix', 'r') as fh:
            lines = fh.readlines()
        for ln in lines[1:]:
            parts = ln.split()
            if len(parts) >= 7:
                rows.append((parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]))
    except Exception as e:
        log('parse unix ERR %s' % e)
    return rows


def try_connect(name, is_abstract, socktype=socket.SOCK_STREAM, timeout=2.0):
    """尝试连接 unix socket, 返回 (ok, err)"""
    try:
        s = socket.socket(socket.AF_UNIX, socktype)
        s.settimeout(timeout)
        addr = name if not is_abstract else '\0' + name[1:]
        s.connect(addr)
        s.close()
        return True, 'OK'
    except Exception as e:
        return False, str(e)[:120]


def probe_stream(name, is_abstract):
    """连接成功后发 HTTP GET 探测"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(3)
        addr = name if not is_abstract else '\0' + name[1:]
        s.connect(addr)
        req = b'GET / HTTP/1.1\r\nHost: unix\r\nConnection: close\r\n\r\n'
        s.sendall(req)
        data = b''
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 8192:
                    break
        except socket.timeout:
            pass
        s.close()
        return data[:800]
    except Exception as e:
        return ('PROBE_ERR %s' % e).encode()


def main():
    log('=== CHK7 PHASE1 /proc/net/unix 全表 ===')
    rows = parse_unix_table()
    log('total rows: %d' % len(rows))
    abstract = []
    fs_paths = []
    for r in rows:
        path = r[6]
        if path.startswith('@'):
            abstract.append(r)
        elif path:
            fs_paths.append(r)
    for r in rows:
        log('  %s type=%s st=%s inode=%s path=%s' % (r[0], r[3], r[4], r[5], r[6][:100]))

    log('=== CHK7 PHASE2 抽象 socket 连接探测 ===')
    for r in abstract:
        name = r[6]
        t = r[3]
        ok, err = try_connect(name, True)
        log('abs %s type=%s connect: %s %s' % (name, t, ok, err))
        if ok and t == '0001':  # STREAM
            resp = probe_stream(name, True)
            log('abs %s HTTP resp: %s' % (name, resp[:400]))
        time.sleep(0.3)

    log('=== CHK7 PHASE3 文件系统 unix socket 存在性 ===')
    for r in fs_paths:
        path = r[6]
        exists = os.path.exists(path)
        log('fs %s exists=%s' % (path, exists))

    log('CHK7_DONE')
    f.close()


if __name__ == '__main__':
    main()
