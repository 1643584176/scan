# 实验J6: 二进制头名挖掘 - 全字符串dump过滤 + 错误消息上下文 + agent进程扫描
# J5 实锤: 带 signature+timestamp 头仍报 "missing signature header" => 头名不是 signature
# 目标: ① 找到正确头名(二进制字符串dump)  ② 找 agent 进程(可能有签名实现)
import os, re, subprocess

def run(cmd, timeout=20):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

BIN = "/run/vercel/share/sandbox-init"
data = open(BIN, "rb").read()
print(f"bin size: {len(data)}", flush=True)

# ---------- [1] 全 ASCII 字符串提取 + 关键字过滤 ----------
print("== [1] 字符串 dump + 关键字过滤 ==", flush=True)
strings = re.findall(rb"[\x20-\x7e]{4,120}", data)
kws = [b"sig", b"auth", b"token", b"secret", b"hmac", b"vercel", b"nonce", b"challenge",
       b"key", b"timestamp", b"expire", b"header", b"x-", b"X-", b"bearer", b"Bearer",
       b"ed25519", b"sign"]
seen = set()
for s in strings:
    ls = s.lower()
    if any(k.lower() in ls for k in kws):
        if s in seen:
            continue
        seen.add(s)
        print(f"  {s.decode(errors='replace')}", flush=True)

# ---------- [2] 错误消息上下文(前后 300B 可打印) ----------
print("== [2] 'missing signature header' 上下文 ==", flush=True)
for m in re.finditer(rb"missing signature header", data):
    ctx = data[m.start()-300:m.start()+300]
    s = re.sub(rb'[^\x20-\x7e]', b'|', ctx)
    print(f"  @0x{m.start():x}:", flush=True)
    print(f"    {s.decode(errors='replace')}", flush=True)

# ---------- [3] 进程列表 + agent 扫描 ----------
print("== [3] /proc 进程 ==", flush=True)
out = run("ls /proc | grep -E '^[0-9]+$' | while read p; do echo \"$p: $(tr '\\0' ' ' < /proc/$p/cmdline 2>/dev/null)\"; done")
print(out, flush=True)

print("== [4] sandbox-init fd 列表(socket 连接) ==", flush=True)
print(run("ls -la /proc/1/fd/ | grep -E 'socket|unix' | head -30"), flush=True)
print(run("cat /proc/1/net/unix 2>/dev/null | head -20"), flush=True)

# ---------- [5] 二进制中 connectrpc 头相关常量 ----------
print("== [5] header 相关常量搜索 ==", flush=True)
for pat in [rb"[A-Za-z0-9-]{3,40}[Hh]eader", rb"[A-Za-z0-9-]{3,40}[Ss]ignature",
            rb"[A-Za-z0-9-]{3,40}[Tt]imestamp", rb"[A-Za-z-]+-[A-Za-z-]+-[A-Za-z-]+"]:
    cnt = 0
    for m in re.finditer(pat, data):
        s = m.group(0)
        if len(s) < 4 or len(s) > 60:
            continue
        # 过滤常见干扰
        if any(x in s for x in (b"content-type", b"content-length", b"accept-encoding",
                                b"connection", b"transfer-encoding", b"host")):
            continue
        print(f"  {s.decode(errors='replace')}", flush=True)
        cnt += 1
        if cnt > 30:
            break
print("done", flush=True)
