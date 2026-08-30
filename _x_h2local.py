# -*- coding: utf-8 -*-
"""本地对照: 同一 h2 帧逻辑直连 httpbin.org (区分帧 bug vs 代理行为)"""
import socket, ssl

def hp_lit(name_idx, value):
    v = value.encode()
    return bytes([0x40 | name_idx, len(v)]) + v

def build_headers(stream, authority, path, end_stream=True):
    blocks = [b'\x82', b'\x87']
    blocks.append(hp_lit(1, authority))
    blocks.append(hp_lit(4, path))
    h = b''.join(blocks)
    flags = 0x04 | (0x01 if end_stream else 0)
    return b'\x00\x00' + bytes([len(h)]) + bytes([0x01, flags]) + stream.to_bytes(4, 'big') + h

def read_frame(s):
    hdr = b''
    while len(hdr) < 9:
        d = s.recv(9 - len(hdr))
        if not d: return None
        hdr += d
    ln = int.from_bytes(hdr[0:3], 'big')
    body = b''
    while len(body) < ln:
        d = s.recv(ln - len(body))
        if not d: return None
        body += d
    return hdr[3], hdr[4], hdr[5:9], body

def h2_get(authority, path='/anything'):
    try:
        ctx = ssl.create_default_context()
        ctx.set_alpn_protocols(['h2'])
        s = ctx.wrap_socket(socket.create_connection(('httpbin.org', 443), timeout=8),
                            server_hostname='httpbin.org')
        print('ALPN', s.selected_alpn_protocol(), flush=True)
        s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')  # connection preface
        s.sendall(b'\x00\x00\x00\x04\x00\x00\x00\x00\x00')  # 空 SETTINGS
        s.sendall(build_headers(1, authority, path))
        data = b''
        s.settimeout(8)
        try:
            while len(data) < 800:
                f = read_frame(s)
                if not f: break
                if f[0] == 4 and not (f[1] & 1):
                    s.sendall(b'\x00\x00\x00\x04\x01\x00\x00\x00\x00\x00')  # ACK
                if f[0] == 0:
                    data += f[3]
                if f[0] == 7:
                    print('GOAWAY', f[3][:20], flush=True)
                    break
        except Exception as e:
            print('RECV_ERR', type(e).__name__, flush=True)
        print('AUTH=%s BODY_HEAD=%r' % (authority, data[:160]), flush=True)
        s.close()
    except Exception as e:
        print('AUTH=%s ERR %s %s' % (authority, type(e).__name__, str(e)[:80]), flush=True)

h2_get('httpbin.org')
print('LOCAL_DONE', flush=True)
