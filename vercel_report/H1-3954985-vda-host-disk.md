# H1 Report #3954985 — Vercel Sandbox escape: user code can read/write the host rootfs block device /dev/vda

> 状态: **Not Applicable**(报告者自证后撤回 self-close)
> 提交: 2026-08-20(8 days ago) | 关闭: 2026-08-21(7 days ago)
> 官方无实质判定评论(仅 standard triage 回复)

## Report (原文)

### Summary
Any user code inside a Vercel Sandbox can open /dev/vda (254:0) with O_RDWR and read/write the entire host rootfs disk (33GB XFS). The sandbox's own rootfs is a different device (/dev/vdb 254:16); /dev/vda carries the host bind-mount sources (/etc/hosts, /etc/resolv.conf, /volumes/run/vercel/share, /run/cell/ca-cert.pem). Host-only dirs (/run/cell, /volumes, /opt/vercel) are invisible in the sandbox FS — reachable only via the raw device node.

### Steps To Reproduce
1. cat /proc/partitions → 254:0 vda (host) + 254:16 vdb (sandbox rootfs)
2. cat /proc/self/mountinfo → sandbox / = 254:16 /dev/vdb; all host bind-mounts come from 254:0 /dev/root (= vda)
3. ls /run/cell /volumes /opt/vercel → all NOT FOUND inside sandbox FS
4. Read host disk: dd if=/dev/vda bs=4096 count=1 | xxd → XFSB superblock (full 33GB readable)
5. Write test (512B at offset outside XFS boundary, restored after): open O_RDWR: OK → wrote 512 → fsync: OK → READBACK match: True → RESTORE match: True (real disk write, not COW)

### Impact
- Read: full host rootfs disclosure — celld configs/runtime (/run/cell, /opt/vercel/celld-init.sh), all /volumes data, /etc/passwd, celld.toml/xkernel.toml located on disk
- Write: verified at block level → modify host startup scripts for host RCE, corrupt host FS, persistent across sandboxes (bind-mount source is this disk)
- Breaks the VM-isolation promise; ca-cert.pem mounted into every sandbox lives on this disk

### Root cause
Sandbox /dev exposes the host rootfs block device (254:0) alongside the sandbox's own (254:16), with no device-cgroup/seccomp restriction on block-device access.

### Suggested fix
Remove the /dev/vda node from sandboxes (keep only /dev/vdb); add device-cgroup denying non-sandbox block devices.

### Attachments
- F6509501: exp_j36_out.txt
- F6509502: exp_j37b_out.txt
- F6509569: vercel-sandbox-host-disk-poc.zip (PoC archive)

## Timeline · 官方回复

### Bot — changed status to Needs more info (8 days ago)
> This report was automatically moved to 'Needs More Info' state because the following required item is missing:
> • Archive file with Proof-of-Concept (.zip, .rar, .7z, etc.)
> Please provide this information to help triage efforts. Note: All vulnerability reports must include an archive file (zip, tar.gz, rar, 7z, etc.) containing working proof-of-concept code that demonstrates the issue.

### base_alert — changed status to New (8 days ago)
Added PoC archive. Run python3 poc_host_disk_access.py inside a Vercel Sandbox - it demonstrates the host rootfs device exposure (steps 1-4) and the verified write capability with immediate restore (step 5, limited to the unused region beyond the XFS filesystem boundary).

### base_alert — closed the report, status → Not Applicable (7 days ago)
> After submission I ran an additional cross-sandbox test: wrote 512 bytes to /dev/vda, called fsync (both succeeded), then read the same block from a freshly created sandbox — the write was not visible. This shows /dev/vda in each sandbox is a private snapshot/COW view rather than the live host disk, so the "persistent host write / host compromise" claims do not hold. The remaining capability (reading sandbox image contents, no sensitive assets found) does not meet the bar for a valid vulnerability. Withdrawing this report.

### vercel-triage — comment (7 days ago)
> Thank you for your report. We have started our analysis and aim to triage it within 5 business days of submission; in all cases we will get back to you before October 1, 2026, when our triage window ends (see Response targets in the program policy). If we need more information to reproduce your finding, we will ask on this report.

## 判定要点(供复盘)

- **报告者自证**:/dev/vda 跨沙箱写不可见 → 每沙箱私有 COW/快照视图,**非 live host disk** → 持久 host 写/host 妥协主张不成立
- 剩余能力(读沙箱镜像内容,无敏感资产)不达有效漏洞门槛 → 主动撤回
- 教训:提交后补测是关键——"写入 vsock CLOSED/双沙箱 NOT SHARED"类负面证据应**先于提交**验证,而非提交后自证
