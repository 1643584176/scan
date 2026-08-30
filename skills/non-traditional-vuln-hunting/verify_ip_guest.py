# -*- coding: utf-8 -*-
"""verify_ip: 验证 tcp6 表原始格式与 IP 解析
1) 打印 /proc/net/tcp6 原始行
2) 打印 /proc/net/tcp 原始行
3) 尝试连接候选 IP:23456/33090 确认服务面
输出落盘 + 哨兵 VIP_DONE"""
import os, time, socket

OUT = '/vercel/sandbox/vip.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def try_conn(ip, port, timeout=2):
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.close()
        return True
    except Exception as e:
        return str(e)[:80]


def main():
    log('=== VIP /proc/net/tcp6 原始行 ===')
    try:
        with open('/proc/net/tcp6', 'r') as fh:
            for ln in fh.readlines():
                log('RAW6: %s' % ln.strip()[:200])
    except Exception as e:
        log('tcp6 ERR %s' % e)

    log('=== VIP /proc/net/tcp 原始行 ===')
    try:
        with open('/proc/net/tcp', 'r') as fh:
            for ln in fh.readlines():
                log('RAW4: %s' % ln.strip()[:200])
    except Exception as e:
        log('tcp ERR %s' % e)

    log('=== VIP 连接测试 ===')
    # 从 tcp6 表提取的地址段
    candidates = ['127.0.0.1', '::1']
    # 尝试解析 v4 候选: 从 tcp6 原始行解析
    try:
        with open('/proc/net/tcp6', 'r') as fh:
            for ln in fh.readlines()[1:]:
                parts = ln.split()
                if len(parts) >= 10:
                    laddr = parts[1]
                    lport = int(laddr.split(':')[-1], 16)
                    # 地址 = 去掉端口后的部分
                    addr_hex = laddr.rsplit(':', 1)[0].replace(':', '')
                    if len(addr_hex) >= 8 and addr_hex[-8:].replace('0', '') != '':
                        ip = '%d.%d.%d.%d' % (int(addr_hex[-8:-6], 16), int(addr_hex[-6:-4], 16),
                                              int(addr_hex[-4:-2], 16), int(addr_hex[-2:], 16))
                        candidates.append(ip)
    except Exception as e:
        log('parse ERR %s' % e)

    for ip in candidates:
        for port in [23456, 33090, 34121, 22, 80, 443]:
            r = try_conn(ip, port)
            log('conn %s:%d -> %s' % (ip, port, r))
        time.sleep(0.3)

    log('VIP_DONE')
    f.close()


if __name__ == '__main__':
    main()
