> # ⚠️ 已撤回 (WITHDRAWN 2026-08-21)
> **撤回原因**：j171 跨沙箱验证证伪“写宿主磁盘”声明——沙箱 A 写 /dev/vda + fsync 成功后，全新沙箱 B 读同一块为全零。/dev/vda 是每沙箱私有视图（只读镜像层 + COW），写不跨沙箱，不存在 persistent host write / host RCE。剩余能力（读镜像内容）无敏感资产，按 Vercel 挑战规则（需真正逃逸/凭据窃取；“仅到 guest OS 不算”）不构成漏洞。主动撤回（Not a vulnerability）。
> **教训**：j37b “写→fsync→读回一致”仅证明写私有副本生效（COW 陷阱）；提交前必须做跨实例验证。

# Title
Vercel Sandbox escape: user code can read/write the host rootfs block device /dev/vda

# Asset
Vercel Sandbox (HackerOne challenge)

# Severity
CRITICAL

# Weakness
CWE-653 Improper Isolation or Compartmentalization (sandbox escape)

# Summary
Any user code inside a Vercel Sandbox can open `/dev/vda` (254:0) with O_RDWR and read/write the **entire host rootfs disk** (33GB XFS). The sandbox's own rootfs is a different device (`/dev/vdb` 254:16); `/dev/vda` carries the host bind-mount sources (`/etc/hosts`, `/etc/resolv.conf`, `/volumes/run/vercel/share`, `/run/cell/ca-cert.pem`). Host-only dirs (`/run/cell`, `/volumes`, `/opt/vercel`) are invisible in the sandbox FS — reachable only via the raw device node.

# Steps To Reproduce
1. `cat /proc/partitions` → `254:0 vda` (host) + `254:16 vdb` (sandbox rootfs)
2. `cat /proc/self/mountinfo` → sandbox `/` = `254:16 /dev/vdb`; all host bind-mounts come from `254:0 /dev/root` (= vda)
3. `ls /run/cell /volumes /opt/vercel` → all NOT FOUND inside sandbox FS
4. Read host disk: `dd if=/dev/vda bs=4096 count=1 | xxd` → `XFSB` superblock (full 33GB readable)
5. Write test (512B at offset outside XFS boundary, restored after):
   `open O_RDWR: OK → wrote 512 → fsync: OK → READBACK match: True → RESTORE match: True` (real disk write, not COW)

# Impact
- Read: full host rootfs disclosure — celld configs/runtime (`/run/cell`, `/opt/vercel/celld-init.sh`), all `/volumes` data, `/etc/passwd`, `celld.toml`/`xkernel.toml` located on disk
- Write: verified at block level → modify host startup scripts for host RCE, corrupt host FS, persistent across sandboxes (bind-mount source is this disk)
- Breaks the VM-isolation promise; `ca-cert.pem` mounted into every sandbox lives on this disk

# Root cause
Sandbox `/dev` exposes the host rootfs block device (254:0) alongside the sandbox's own (254:16), with no device-cgroup/seccomp restriction on block-device access.

# Suggested fix
Remove the `/dev/vda` node from sandboxes (keep only `/dev/vdb`); add device-cgroup denying non-sandbox block devices.
