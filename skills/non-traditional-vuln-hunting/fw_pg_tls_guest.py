# -*- coding: utf-8 -*-
"""fw_pg_tls: TLS 包装 PG 指纹 (StartupMessage over TLS, 不认证)
1) connect + SSLRequest -> S -> TLS handshake (ssl module)
2) TLS 内发 StartupMessage -> 读认证请求类型 (AuthenticationOk/PasswordRequired 等)
3) 对照: 非 TLS 直连 StartupMessage (应 RST) 已在 fw_pg_fp 完成
输出落盘 + 哨兵 FWTLS_DONE"""
import socket, time, struct, ssl

OUT = '/vercel/sandbox/fwtls.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def pg_tls_startup(ip, port=5432, t=5, rt=4):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        # SSLRequest
        s.sendall(struct.pack('!II', 8, 80877103))
        resp = s.recv(1)
        if resp != b'S':
            s.close()
            return 'SSL_NEG_FAIL %r' % resp
        # TLS handshake (SNI = IP 字符串, 不验证证书)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ts = ctx.wrap_socket(s, server_hostname=ip)
        # StartupMessage over TLS
        params = {'user': 'probe_user', 'database': 'probe_db',
                  'application_name': 'vercel-sandbox-probe', 'client_encoding': 'UTF8'}
        body = struct.pack('!I', 196608)
        for k, v in params.items():
            body += k.encode() + b'\x00' + v.encode() + b'\x00'
        body += b'\x00'
        ts.sendall(struct.pack('!I', len(body) + 4) + body)
        ts.settimeout(rt)
        d = b''
        try:
            while True:
                ch = ts.recv(4096)
                if not ch:
                    break
                d += ch
                if len(d) > 1024:
                    break
        except socket.timeout:
            pass
        ts.close()
        if not d:
            return 'TLS_OK_NODATA'
        msgs = []
        off = 0
        while off + 5 <= len(d):
            mtype = chr(d[off])
            mlen = struct.unpack('!I', d[off + 1:off + 5])[0]
            mbody = d[off + 5:off + 1 + mlen]
            msgs.append('%s:%s' % (mtype, mbody[:150]))
            off += 1 + mlen
        return 'TLS_MSGS %s' % ' | '.join(msgs)
    except ssl.SSLError as e:
        return 'SSL_ERR:%s' % str(e)[:100]
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
    log('=== P1 TLS PG StartupMessage (9 采样) ===')
    for ip in ips:
        log('%s -> %s' % (ip, pg_tls_startup(ip)))
        time.sleep(0.4)
    log('FWTLS_DONE')
    f.close()


if __name__ == '__main__':
    main()
