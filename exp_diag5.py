# 抓 openssl s_client 的真实 ClientHello,与我的构造逐字节对比
import subprocess, re, sys

sys.path.insert(0, '.')

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='replace') + r.stderr.decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

# 1. 抓 openssl 标准 CH(-msg 打印握手字节)
out = run("echo | timeout 8 openssl s_client -connect 1.1.1.1:443 -servername example.com -msg 2>&1 | head -160")
m = re.search(r'>>> TLS [^,]+, Handshake, ClientHello \(\d+\):\n(.*?)(?=\n<<<|\n>>>|\Z)', out, re.S)
if not m:
    print("NO CH captured. output head:")
    print(out[:1200])
    sys.exit(0)
hexbytes = []
for line in m.group(1).splitlines():
    parts = line.split()
    if len(parts) >= 3 and parts[1] == '-':
        for p in parts[2:]:
            if re.fullmatch(r'[0-9a-fA-F]{2}', p):
                hexbytes.append(p)
ossl_ch = bytes.fromhex(''.join(hexbytes))
print(f"openssl CH len: {len(ossl_ch)}")
print("openssl CH:", ossl_ch[:120].hex())

# 2. 我的 CH
import exp_d3 as m3
my_ch = m3.clienthello(["example.com"])
print(f"my CH len: {len(my_ch)}")
print("my CH    :", my_ch[:120].hex())

# 3. 结构对比:解析 openssl CH 的字段
def parse(ch):
    """返回 (version, random, sid_len, ciphers, comp, exts: {type: (data)})"""
    i = 5  # 跳过 record 头
    assert ch[i] == 1
    hslen = int.from_bytes(ch[i+1:i+4], 'big')
    body = ch[i+4:i+4+hslen]
    j = 0
    ver = body[j:j+2]; j += 2
    rnd = body[j:j+32]; j += 32
    sid_len = body[j]; j += 1
    sid = body[j:j+sid_len]; j += sid_len
    cip_len = int.from_bytes(body[j:j+2], 'big'); j += 2
    cips = body[j:j+cip_len]; j += cip_len
    comp_len = body[j]; j += 1
    comp = body[j:j+comp_len]; j += comp_len
    ext_len = int.from_bytes(body[j:j+2], 'big'); j += 2
    exts = {}
    end = j + ext_len
    while j < end:
        t = int.from_bytes(body[j:j+2], 'big')
        l = int.from_bytes(body[j+2:j+4], 'big')
        exts[t] = body[j+4:j+4+l]
        j += 4 + l
    return ver, rnd, sid, cips, comp, exts

ov, ornd, osid, ocips, ocomp, oexts = parse(ossl_ch)
mv, mrnd, msid, mcips, mcomp, mexts = parse(my_ch)

print(f"\nversion: openssl={ov.hex()} mine={mv.hex()} {'OK' if ov==mv else 'DIFF'}")
print(f"random:  openssl={ornd[:4].hex()}... mine={mrnd[:4].hex()}... (固定值,允许差异)")
print(f"sid_len: openssl={len(osid)} mine={len(msid)}")
print(f"ciphers: openssl {len(ocips)//2}个={ocips.hex()} mine {len(mcips)//2}个={mcips.hex()}")
print(f"comp:    openssl={ocomp.hex()} mine={mcomp.hex()}")
print(f"\nopenssl exts({len(oexts)}):")
for t, d in sorted(oexts.items()):
    print(f"  type={t:4d} len={len(d):3d} data={d[:24].hex()}")
print(f"mine exts({len(mexts)}):")
for t, d in sorted(mexts.items()):
    print(f"  type={t:4d} len={len(d):3d} data={d[:24].hex()}")
