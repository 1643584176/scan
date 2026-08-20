# PoC: Vercel Sandbox host rootfs disk access

## How to run

Create a Vercel Sandbox, then run:

```
python3 poc_host_disk_access.py
```

No special setup is required - the sandbox's default environment
(uid 1000 with full capabilities) is sufficient.

## What it demonstrates

| Step | Evidence |
|---|---|
| [1] | `/dev/vda` (254:0) and `/dev/vdb` (254:16) are two separate block devices |
| [2] | Sandbox rootfs `/` is mounted from `/dev/vdb` (254:16); all host bind-mounts (`/etc/hosts`, `/etc/resolv.conf`, `/volumes/run/vercel/share`, `/run/cell/ca-cert.pem`) come from `/dev/root` = `/dev/vda` (254:0) |
| [3] | Host-only directories `/run/cell`, `/volumes`, `/opt/vercel` do NOT exist in the sandbox filesystem |
| [4] | The XFS superblock of the HOST rootfs is readable through `/dev/vda` (full 33 GB disk readable) |
| [5] | The device opens with `O_RDWR`; a 512-byte write outside the XFS filesystem boundary is confirmed by fsync + readback (`READBACK match: True`), then the original bytes are restored (`RESTORE match: True`) |

## Safety note on the write test

The write test is deliberately minimal and non-destructive:

- The target offset is in the **unused tail region beyond the XFS filesystem boundary** (the disk is ~8 MB larger than the filesystem; the test writes in the middle of that gap) - no filesystem structure is touched.
- Exactly 512 bytes are written, verified by readback, then the original bytes are restored and verified (`RESTORE match: True`).
- Surrounding 1 KB on both sides is confirmed untouched.

This proves the sandbox can write the host disk without actually modifying any host data.

## Expected output (key lines)

```
===== [4] READ the host rootfs disk (superblock) =====
magic=b'XFSB' blocksize=4096 dblocks=8648704 (filesystem size ~33.0 GiB)

===== [5] WRITE test ... =====
open O_RDWR: OK
wrote 512 bytes, fsync OK
READBACK match (write really hit the host disk, not COW): True
RESTORE match (original bytes restored): True

RESULT: sandbox user code can READ and WRITE the host rootfs block device
```

## Impact summary

- **Read**: entire host rootfs (33 GB XFS) disclosed - celld runtime (`/run/cell`), host volumes (`/volumes`), host startup scripts (`/opt/vercel/celld-init.sh`), service configs, `/etc/passwd`, `/etc/hosts`, `/etc/resolv.conf`.
- **Write**: host rootfs tampering - host startup script modification for host RCE, filesystem corruption, persistence across sandboxes (this disk is the bind-mount source for every sandbox).
- Breaks the VM-level isolation promise of the sandbox.
