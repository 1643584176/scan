import subprocess, time

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='replace') + r.stderr.decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("openssl:", run("openssl version"))
print("req:", run("openssl req -x509 -newkey rsa:2048 -keyout /tmp/k.pem -out /tmp/c.pem -days 1 -nodes -subj '/CN=example.com' 2>&1 | tail -3"))
print("pem files:", run("ls -la /tmp/k.pem /tmp/c.pem 2>&1"))
print("start srv:", run("(openssl s_server -accept 127.0.0.1:4443 -cert /tmp/c.pem -key /tmp/k.pem -msg > /tmp/srv.log 2>&1 &); sleep 2; cat /tmp/srv.log | head -20; echo '---'; ps aux | grep -c s_serve[r]"))
print("listen check:", run("(echo > /dev/tcp/127.0.0.1/4443) 2>&1 && echo OPEN || echo CLOSED"))
