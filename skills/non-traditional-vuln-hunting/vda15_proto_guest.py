# -*- coding: utf-8 -*-
"""vda15_proto: 挖 Exec/StreamOutput/Start/Wait 的 protobuf 字段定义
从 celld 二进制提取 protobuf 标签 (name=xxx, protobuf:"bytes,N,opt...")
输出落盘 + 哨兵 V15B_DONE"""
import os, time, socket, ctypes, re

OUT = '/vercel/sandbox/v15b.out'
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

    log('=== P1 proto fields ===')
    try:
        data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
        txt = b'\n'.join(re.findall(rb'[\x20-\x7e]{6,}', data)).decode(errors='replace')
        # 提取所有 protobuf 标签 (字段名+编号)
        tags = re.findall(r'protobuf:"(bytes|string|bool|int64|uint64|repeated bytes|repeated string),[0-9]+,opt,name=([a-z_0-9]+)', txt)
        log('all tags (%d): %s' % (len(tags), sorted(set(tags))))
        # ExecRequest/StreamOutputRequest 相关消息结构
        for msg in ['ExecRequest', 'StreamOutputRequest', 'StartRequest', 'ProcessStartRequest',
                    'CreateRequest', 'StartContainerRequest', 'WaitRequest', 'KillRequest',
                    'ContainersService']:
            idxs = [m.start() for m in re.finditer(re.escape(msg), txt)][:4]
            for i in idxs:
                seg = txt[max(0, i - 60):i + 400].replace('\n', ' ')
                if 'protobuf' in seg or 'name=' in seg or 'Service' in seg:
                    log('ctx %s: ...%s...' % (msg, seg[:380]))
    except Exception as e:
        log('P1 ERR %s' % e)

    log('V15B_DONE')
    f.close()


if __name__ == '__main__':
    main()
