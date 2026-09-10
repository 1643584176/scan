# -*- coding: utf-8 -*-
"""ET50: DB-port matrix (TCP handshake only) against discovered DB-ish hosts"""
import socket, threading

HOSTS = [
    "pg.ticketnew.com",
    "kibana.zomans.com",
    "grafana.zomans.com",
    "grafana.grofer.io",
    "grafana.grofers.com",
    "superset.zomans.com",
    "superset.grofer.io",
    "reports.grofer.io",
    "internal.grofer.io",
    "admin.district.in",
    "admin.edition.in",
    "admin.zomans.com",
    "api2.blinkit.com",
    "api3.blinkit.com",
]
PORTS = [5432, 3306, 27017, 6379, 9200, 5601, 5984, 8123, 8086, 7474, 9092]

lock = threading.Lock()
results = []

def check(host, port):
    try:
        s = socket.create_connection((host, port), timeout=6)
        s.close()
        with lock:
            results.append((host, port, "OPEN"))
    except Exception:
        pass

threads = []
for h in HOSTS:
    for p in PORTS:
        t = threading.Thread(target=check, args=(h, p), daemon=True)
        t.start()
        threads.append(t)
        if len(threads) >= 40:
            for t in threads:
                t.join(20)
            threads = []
for t in threads:
    t.join(20)

print("== open DB-ish ports (%d host x %d port checks) ==" % (len(HOSTS), len(PORTS)))
for h, p, st in sorted(results):
    print("%-32s :%d %s" % (h, p, st))
if not results:
    print("(none open)")
print("done", flush=True)
