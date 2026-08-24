# 辅助脚本: 打印本机 IP(供 exp_i17_run.py 正则解析)
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
print(f"本机IP: {s.getsockname()[0]}", flush=True)
