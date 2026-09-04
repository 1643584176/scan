# pg_repack 报告补充 comment(2026-09-03 验证)

用途:粘贴到 H1 已提交报告评论区(标题 "Netlify Postgres: privesc to cloud_admin superuser via pg_repack")

---

**Additional impact validation — OS-level command execution via the same chain**

Following up on this report, I validated the post-exploitation impact more precisely. All tests were read-only/zero-side-effect, on my own site's database.

**Setup**: Rebuilt the same trigger chain (k_src -> repack_trigger -> repack.log_{oid} -> t_log -> k_evil -> `k_run` SECURITY DEFINER function owned by `cloud_admin`) on my site.

**Baseline** — direct execution as `netlifydb_owner` (no chain) is blocked:
```
copy (select 'x') to program 'false'
-> ERROR: permission denied to COPY to or from an external program
```

**Exploit context** — same statement executed through `k_run` (runs as `cloud_admin`):
```
select * from k_run($$copy (select 'x') to program 'false'$$)
-> ERROR: program "false" failed
```
`false` exiting non-zero is only reported if the OS command was actually spawned.

```
select * from k_run($$copy (select 'x') to program 'true'$$)
-> ERROR: could not close pipe to external command: Broken pipe
```
(`true` exited immediately — again, command execution confirmed.)

**Impact**: The privilege chain is not limited to SQL-level `pg_read_file` (as originally demonstrated with `neon.storage_token`); it gives arbitrary OS command execution inside the compute container as the `postgres` OS user — arbitrary file writes, `/proc` inspection (process environments, network state), etc. Data exfiltration is possible through the existing query return channel (`pg_read_file` + `database-query`).

**Mitigating factor (observed)**: the compute has no working outbound network — DNS resolution fails, direct-IP TCP connects fail, and RFC1918 targets hang (blackhole). Lateral movement from the container appears blocked; impact stays within the single site's compute.

Cleaned up all test objects afterwards (extension dropped, no residue).

---

验证记录(脚本):
- D:\scan\netlify_report\_dbq_copyprog.py(搭链 + COPY PROGRAM + dblink 出站 + 清理,执行成功)
- D:\scan\netlify_report\_dbq_copy_direct.py(owner 直接执行对照:permission denied)
