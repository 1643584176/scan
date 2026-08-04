# -*- coding: utf-8 -*-
"""pt10: DoH 备用 IP 发现 + TCP 连通性测试"""
import json
import socket
import ssl
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def doh_a(host):
    url = f"https://cloudflare-dns.com/dns-query?name={host}&type=A"
    req = urllib.request.Request(url, headers={'Accept': 'application/dns-json'})
    try:
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, context=ctx, timeout=8)
        d = json.loads(resp.read())
        return [a['data'] for a in d.get('Answer', []) if a.get('type') == 1]
    except Exception as e:
        return [f'ERR:{e}']


def tcp_test(ip, port=443, timeout=5):
    try:
        t0 = time.time()
        s = socket.create_connection((ip, port), timeout=timeout)
        s.close()
        return f"OK {time.time()-t0:.2f}s"
    except Exception as e:
        return f"FAIL {type(e).__name__}"


def main():
    hosts = ['api.steampowered.com', 'steamcommunity.com', 'store.steampowered.com',
             'help.steampowered.com', 'partner.steamgames.com', 'www.playartifact.com']
    for h in hosts:
        ips = doh_a(h)
        print(f"\n### {h}")
        print(f"   DoH A 记录: {ips}")
        for ip in ips[:8]:
            if ip.startswith('ERR'):
                print(f"   DoH 失败: {ip}")
                break
            print(f"   {ip:18s} -> {tcp_test(ip)}")
            time.sleep(0.3)


if __name__ == '__main__':
    main()
