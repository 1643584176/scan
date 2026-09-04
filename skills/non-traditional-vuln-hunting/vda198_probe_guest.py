# -*- coding: utf-8 -*-
"""v197 payload (guest): raw socket 抓宿主 netns 流量 (TCP SYN + DNS qname)
观测 CreateSnapshot 上传请求是否真实发出
输出 /vercel/sandbox/v198s.out"""
import socket, struct, time, signal

OUT = '/vercel/sandbox/v198s.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)


def log(s, maxlen=2000):
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


log('=== sniff start ===')
try:
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
    s.settimeout(2)
    log('AF_PACKET OK')
except Exception as e:
    log('AF_PACKET EXC %s' % e)
    s = None

end = time.time() + 210
n = 0
while time.time() < end and s is not None:
    try:
        d = s.recv(65536)
    except socket.timeout:
        continue
    except Exception as e:
        log('RECV EXC %s' % e)
        break
    if len(d) < 40:
        continue
    try:
        proto = struct.unpack('!H', d[12:14])[0]
        if proto == 0x0800 and len(d) >= 14 + 20:
            ihl = (d[14] & 0x0f) * 4
            if len(d) < 14 + ihl + 4:
                continue
            src = socket.inet_ntoa(d[14 + 12:14 + 16])
            dst = socket.inet_ntoa(d[14 + 16:14 + 20])
            p = d[14 + 9]
            if p == 6 and len(d) >= 14 + ihl + 20:
                srcp, dstp = struct.unpack('!HH', d[14 + ihl:14 + ihl + 4])
                flags = d[14 + ihl + 13]
                if flags & 0x02:
                    log('SYN %s:%d -> %s:%d' % (src, srcp, dst, dstp))
                    n += 1
            elif p == 17 and len(d) >= 14 + ihl + 8:
                srcp, dstp = struct.unpack('!HH', d[14 + ihl:14 + ihl + 4])
                if dstp == 53 or srcp == 53:
                    try:
                        # DNS 报文在 UDP payload 里, 跳过 8 字节 UDP 头
                        q = d[14 + ihl + 8:]
                        if len(q) > 12:
                            qname = []
                            i = 12
                            while i < len(q) and q[i] != 0:
                                ln = q[i]
                                if ln > 63:
                                    break
                                qname.append(q[i + 1:i + 1 + ln].decode(errors='replace'))
                                i += 1 + ln
                            if qname:
                                log('DNSQ %s:%d -> %s q=%s' % (src, srcp, dst, '.'.join(qname)))
                    except Exception:
                        pass
    except Exception:
        pass
    if n > 200:
        log('SYN limit 200')
        break

if s is not None:
    s.close()
log('V197S_DONE')
f.close()
