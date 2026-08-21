# PoC: Vercel Sandbox init.sock signature bypass

## How to run

Create a Vercel Sandbox, then upload and run the PoC:

```
python3 poc_init_sock_bypass.py id
python3 poc_init_sock_bypass.py sh -c "id && ls -la /dev/vda /dev/vdb && grep Cap /proc/1/status"
```

The sandbox's default environment (uid 1000 with full capabilities, ptrace of
PID 1 allowed) is sufficient. No API token or external credentials are used.

## What it demonstrates

| Step | Evidence |
|---|---|
| [1] | `PTRACE_ATTACH` on PID 1 (`sandbox-init`, owner of `/run/vercel/share/init.sock`) succeeds — no Yama/seccomp restriction from sandbox user code |
| [2] | `PTRACE_POKEDATA` patches the 3 ed25519 signature-verification failure branches to force `err=nil` (Go register ABI) |
| [3] | `SpawnService/Spawn` on the control socket is called with an **arbitrary** `x-signature` (64×0x99) + any timestamp — accepted and executed |
| [4] | Spawned processes inherit `sandbox-init`'s full capability set (CapEff=000001ffffffffff) |
| [5] | Control experiment (fresh sandbox, no patch): the identical request returns `{"error":{"code":"unauthenticated","message":"invalid signature"}}` |

## Expected output (key lines)

```
[*] signature check bypassed (3 sites patched)
uid=1000(vercel-sandbox) gid=1000(vercel-sandbox) groups=1000(vercel-sandbox)
[exit {}]
```

## Additional verified surface

- `SpawnService/Kill` terminates spawned processes (verified: spawned `sleep 60` disappears from `ps`)
- `pidfd_getfd(pidfd_open(1), 7)` duplicates `sandbox-init`'s control-socket fds (host-side connection) into the attacker process
- Spawned processes can `setuid(0)` → real root inside the shared host kernel, and open the host rootfs block device `/dev/vda` O_RDWR (see companion report)

## Files

| File | Content |
|---|---|
| H1-vercel-sandbox-init-sig-bypass.md | Report text |
| poc_init_sock_bypass.py | Working PoC (patch + fake-signature Spawn) |
| exp_j65_sig_bypass_first_ok.txt | First successful fake-signature Spawn (`id`) |
| exp_j75_service_enum_pidfd.txt | Service enumeration (Ping/Kill/Spawn) + pidfd_getfd fd duplication |
| exp_j76_ping_kill.txt | Ping/Kill semantics; Kill terminates a spawned process |
| exp_j77_control_nopatch.txt | Control experiment: `invalid signature` without the patch |
| exp_j78_tool_e2e.txt | End-to-end run of the PoC file inside a sandbox |

## Note

The 3 patch addresses are for the current `sandbox-init` build (non-PIE binary,
fixed addresses). The technique (ptrace + patch failure branches of the
signature check) is build-agnostic; the addresses can be relocated by scanning
the binary for the `ed25519.Verify` failure paths.
