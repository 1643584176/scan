# -*- coding: utf-8 -*-
"""fw_pg_fp: PostgreSQL 只读指纹 (StartupMessage 不认证)
1) 发 StartupMessage -> 收服务端错误/认证请求 (只读, 不发送任何凭据)
2) 多 IP 采样确认一致性
3) 对照: 本沙箱内不存在的服务 (应 RST) + 公网 IP (应超时/拒绝)
输出落盘 + 哨兵 FWFINGER_DONE"""
import socket, time, struct

OUT = '/vercel/sandbox/fwfinger.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def pg_startup(ip, port=5432, t=4, rt=3):
    """PostgreSQL StartupMessage: 协议版本 3.0 + user/database/application_name
    只发送握手, 绝不发送密码/认证响应"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        params = {
            'user': 'probe_user',
            'database': 'probe_db',
            'application_name': 'vercel-sandbox-probe',
            'client_encoding': 'UTF8',
        }
        body = struct.pack('!I', 196608)  # protocol 3.0
        for k, v in params.items():
            body += k.encode() + b'\x00' + v.encode() + b'\x00'
        body += b'\x00'
        pkt = struct.pack('!I', len(body) + 4) + body
        s.sendall(pkt)
        s.settimeout(rt)
        d = b''
        try:
            while True:
                ch = s.recv(4096)
                if not ch:
                    break
                d += ch
                if len(d) > 512:
                    break
        except socket.timeout:
            pass
        s.close()
        if not d:
            return 'NODATA'
        # 解析服务端消息类型
        msgs = []
        off = 0
        while off + 5 <= len(d):
            mtype = chr(d[off])
            mlen = struct.unpack('!I', d[off + 1:off + 5])[0]
            mbody = d[off + 5:off + 1 + mlen]
            msgs.append('%s:%s' % (mtype, mbody[:120]))
            off += 1 + mlen
        return 'MSGS %s' % ' | '.join(msgs)
    except (ConnectionResetError, BrokenPipeError):
        return 'RST'
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


def main():
    ips = ['172.31.0.3', '172.31.0.4', '172.31.0.81', '172.31.0.101', '172.31.0.140',
           '172.31.0.200', '172.31.57.1', '172.31.140.100', '172.31.250.254']
    log('=== P1 PG StartupMessage 指纹 (9 采样) ===')
    for ip in ips:
        log('%s -> %s' % (ip, pg_startup(ip)))
        time.sleep(0.3)

    log('=== P2 对照: 无服务端口 ===')
    log('172.31.0.3:59999 -> %s' % pg_startup('172.31.0.3', 59999))
    log('172.31.0.3:23456 -> %s' % pg_startup('172.31.0.3', 23456))

    log('=== P3 对照: 本沙箱 localhost 5432 (应拒绝) ===')
    log('127.0.0.1:5432 -> %s' % pg_startup('127.0.0.1', 5432))

    log('FWFINGER_DONE')
    f.close()


if __name__ == '__main__':
    main()
