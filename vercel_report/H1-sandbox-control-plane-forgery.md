> **状态: 未提交(评估为 N/A)** — 对照官方判定标准(#3955363/#3965216/#3972961 回复):攻击面(sandbox-init 控制面/密钥材料)已在 Known findings,影响(伪造沙箱内命令结果)停留 own microVM,无 EC2 host 逃逸/跨租户/新 host 写原语 → 不满足提交门槛。存档为技术记录。

# 标题 必填
title: Sandbox Guest Can Hijack Host→init Control Plane (pidfd_getfd) and Forge Command Execution Results — Arbitrary stdout, Exit Codes, and Timing Accepted by the Host Control Plane

# 资产 必填
Asset: https://api.vercel.com/v2/sandboxes (Vercel Sandbox / vercel.com sandboxes)

# 严重程度 必填
Severity: MEDIUM

# 弱点 必填
Weakness: CWE-345 (Insufficient Verification of Data Authenticity) + CWE-284 (Improper Access Control)

# 描述 必填
Description
    ## Summary:
    In a Vercel Sandbox (api.vercel.com/v2/sandboxes), an unprivileged guest process can use `pidfd_open(434)` + `pidfd_getfd(438)` to steal the file descriptors of `sandbox-init` (PID 1, running inside the guest's pid namespace at `/run/vercel/share/sandbox-init`). One of these fds is the LISTEN socket for the host→init control plane (`/run/vercel/share/init.sock`, a Unix domain socket on which the host's `SpawnService` RPC calls arrive).

    By racing `accept()` on the stolen LISTEN fd (hit rate ~25-30% with a 200ms poll), the guest can:
    1. **Eavesdrop** on every host→init `Spawn` request in plaintext (command, args, cwd, `X-Signature`, `X-Timestamp` headers) — verified in run11/run14.
    2. **Inject forged Connect-RPC responses** (a `SpawnEvent` stream encoded as connect-go frames) that the host **unconditionally trusts** — the response direction has no signature/encryption/authenticity protection (only the request direction carries `X-Signature`).

    Forged responses were accepted by the host and surfaced to the API client (the sandbox command API):
    - **Forged stdout data**: `cat /etc/hostname` returned `FAKEHOST-87907494` (attacker-controlled bytes) instead of the real hostname (run15, reproduced twice).
    - **Forged exit code**: `sleep 2; echo done` returned `exitCode: 7, durationMs: 0` — the command never actually ran; the host reported our forged code 7 and 0ms duration (run15). In run14 the same command completed in 0ms with exit 0 (real execution takes 2002ms).
    - **Forged timing**: a 2-second `sleep` completes in 0ms when hijacked (run14 trig 2.2: durationMs 0 vs baseline 2002ms).
    - **Hang injection** (started event without exit): affected `ps` commands produce real stdout but **never receive a completion event** — 5/5 subsequent `ps` triggers were left in a pending state (run15).

    The host also reuses the hijacked connection for subsequent requests (keep-alive, observed via POST-SEND reads of the next `Spawn` request on the same socket), confirming the connection is indistinguishable from a legitimate init connection.

    ## Steps To Reproduce:
    1. Create a sandbox via `POST /v2/sandboxes` (any plan), then start a guest process that runs the attached `pidfd_guest.py`:
       1. `pidfd_open(1)` → pidfd for `sandbox-init`
       2. `pidfd_getfd(pidfd, fd)` for every fd in `/proc/1/fd` → steals LISTEN fd (fd 9, `init.sock`) and 3 established connections (fd 12/13/14, peercred `(0,0,0)` = host process)
       3. Spawn a listener thread: `poll(LISTEN_fd, 200ms)` + `accept4()` — races the host's epoll accept loop (~25-30% hit rate)
       4. On accept: `recv()` the full HTTP request, then `send()` a forged Connect-RPC response:
          - Forged `SpawnEvent{started:{process_id:"1"}}` + `SpawnEvent{stdout:"FAKEHOST-..."}` + `SpawnEvent{exit:{code:0}}` for `cat /etc/hostname` requests
          - Forged `SpawnEvent{started}` + `SpawnEvent{exit:{code:7}}` for `sleep` requests
          - Forged `SpawnEvent{started}` only (hang) for `ps` requests
    2. Issue sandbox commands via `POST /v2/sandboxes/{sid}/commands`:
       1. `bash -c "cat /etc/hostname"` — response contains attacker-injected `FAKEHOST-87907494` instead of the real hostname (reproduced at 1787907494 and 1787907513)
       2. `bash -c "sleep 2; echo done"` — response reports `exitCode: 7, durationMs: 0` (forged; baseline is exit 0, 2002ms)
       3. `bash -c "ps aux | head -3"` — command runs (real stdout arrives) but the completion event never arrives (5/5 triggers left pending)
    3. Control (no hijack): the same commands return the real hostname, `exitCode: 0` with `durationMs: 2002` for sleep, and a normal completion event for ps.

    ## Supporting Material/References:
    * Attacker-side script: `pidfd_guest.py` (v13) — full PHASE1 fd-theft + accept-race + response-forgery implementation
    * Driver: `pidfd_driver.py` — issues the trigger commands and dumps full API responses
    * Experiment logs: `pidfd_run11.log` (eavesdrop), `pidfd_run14.log` (forged stream accepted: sleep 0ms/exit 0), `pidfd_run15.log` (forged stdout FAKEHOST-*, forged exit 7, hang)
    * Protocol reverse-engineering: `probe_init6.py` extracted the full `spawn.proto` descriptor from the sandbox-init binary:
      - `SpawnRequest{command=1, arguments=2, environment=3, working_directory=4}`
      - `SpawnEvent{oneof: started=1(SpawnStarted{process_id}), stdout=2(bytes), stderr=3(bytes), exit=4(ExitStatus{code})}` — server-streaming
      - Forged frame bytes: started `00 00000005 0a030a0131`, stdout `00 00000014 1212 46414b45484f53542d…`, exit0 `00 00000004 22020800`
    * Raw capture of a hijacked request (run14): `POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1`, `User-Agent: connect-go/1.20.0 (go1.25.14)`, `X-Signature: …`, `X-Timestamp: 1787906996`
    * A forged 200 response on the hijacked connection was followed by the host sending the *next* Spawn request on the same socket (POST-SEND read = 431-454B), proving connection reuse / indistinguishable connection

# 影响 必填
Impact:
    A guest process (e.g. malicious code from `npm install` in a dev sandbox, or any sandboxed workload) can fully forge the host's perception of command execution:

    * **Data/result forgery**: attacker-controlled stdout/stderr bytes and exit codes are accepted by the host control plane and streamed verbatim to the sandbox API consumer (developers, CI, automation). Any automation that gates on command results (build success, health checks, provisioning steps, cleanup routines) can be tricked in either direction.
    * **Arbitrary timing**: long-running commands can be reported as instantly finished (0ms), or conversely left perpetually pending via the hang primitive, disrupting workflows that await command completion.
    * **Persistent state corruption**: after a hang injection, subsequent commands of the same class observed no completion events (5/5 in run15), showing the impact can extend beyond the single hijacked request.
    * **Full control-plane eavesdropping**: the guest sees every command the host executes in the sandbox, including the exact `X-Signature` scheme used by the host (per-request, bound to `X-Timestamp`), which is additional attack surface for further research.

    Root causes:
    1. The sandbox allows a guest to reach `sandbox-init`'s fds via `pidfd_getfd` (`/proc/1` is visible, pidfd syscalls are not filtered).
    2. The host→init control plane authenticates only the request direction (`X-Signature`); the response direction has no authenticity/integrity protection, so a hijacker's forged `SpawnEvent` stream is indistinguishable from the real init.

    Suggested fixes:
    1. Block `pidfd_getfd`/`pidfd_open` for guests (seccomp), or hide `/proc/1/fd` and prevent fd theft from `sandbox-init`.
    2. Move `sandbox-init` into a separate pid namespace invisible to guests, or protect its fds (e.g. `close_range` after setup, `O_CLOEXEC` hygiene, dedicated control socket on a host-side mount namespace).
    3. Authenticate the response direction (init signs each response / establishes a per-connection shared secret during handshake), so forged responses are rejected.

# 附件 非必填
Attachments:
  * pidfd_guest.py (attacker script, v13)
  * pidfd_driver.py (trigger driver)
  * pidfd_run11.log / pidfd_run14.log / pidfd_run15.log (evidence logs)
  * probe_init6.py (spawn.proto extraction)
