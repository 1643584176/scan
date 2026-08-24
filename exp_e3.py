# 实验E3: forwardURL 目标 SSRF 测试(复用 expe1 沙箱, 每轮 update policy 后请求)
# 轮次1: forwardURL=http://169.254.169.254  -> 宿主机 AWS IMDS?
# 轮次2: forwardURL=http://127.0.0.1:26661  -> 防火墙/沙箱本机端口
# 轮次3: forwardURL=http://100.64.0.1        -> 内部网关
# 轮次4: forwardURL=http://example.com       -> 公网明文对照
import urllib.request, ssl, sys, json

def fetch(path, label):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = f"https://httpbin.org{path}"
    req = urllib.request.Request(url)
    try:
        r = urllib.request.urlopen(req, context=ctx, timeout=25)
        body = r.read(3000)
        h = dict(r.headers)
        print(f"== [{label}] {path}: status={r.status} server={h.get('Server')} len={len(body)}")
        print("   body[:400]:", body[:400])
        return r.status
    except urllib.error.HTTPError as e:
        body = e.read(500)
        print(f"== [{label}] {path}: HTTPError={e.code} server={e.headers.get('Server')}")
        print("   body[:300]:", body[:300])
        return e.code
    except Exception as e:
        print(f"== [{label}] {path}: EXC {type(e).__name__}: {e}")
        return None

label = sys.argv[1] if len(sys.argv) > 1 else "?"
fetch("/latest", label)
