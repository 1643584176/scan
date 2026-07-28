from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from assettrace.config import Settings
from assettrace.models import AssetSnapshot, FetchResult, FindingDraft
from assettrace.urls import canonicalize_url, hostname


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


class Repository:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.ensure_directories()
        self.init_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.settings.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init_schema(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    root_url TEXT NOT NULL UNIQUE,
                    scope_host TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS scan_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    root_url TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    summary_json TEXT NOT NULL DEFAULT '{}',
                    error_message TEXT NOT NULL DEFAULT '',
                    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT
                );

                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    canonical_url TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'discovered',
                    fetch_error TEXT NOT NULL DEFAULT '',
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_checked_at TEXT,
                    UNIQUE(project_id, canonical_url)
                );

                CREATE TABLE IF NOT EXISTS asset_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL REFERENCES assets(id),
                    fingerprint_sha256 TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    body_path TEXT NOT NULL,
                    final_url TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    headers_json TEXT NOT NULL,
                    redirect_chain_json TEXT NOT NULL DEFAULT '[]',
                    fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_confirmed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(asset_id, fingerprint_sha256)
                );

                CREATE TABLE IF NOT EXISTS asset_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    source_asset_id INTEGER NOT NULL REFERENCES assets(id),
                    target_asset_id INTEGER NOT NULL REFERENCES assets(id),
                    relation TEXT NOT NULL,
                    first_seen_run_id INTEGER REFERENCES scan_runs(id),
                    last_seen_run_id INTEGER REFERENCES scan_runs(id),
                    UNIQUE(project_id, source_asset_id, target_asset_id, relation)
                );

                CREATE TABLE IF NOT EXISTS analysis_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL REFERENCES scan_runs(id),
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    asset_id INTEGER NOT NULL REFERENCES assets(id),
                    revision_id INTEGER NOT NULL REFERENCES asset_revisions(id),
                    detector_key TEXT NOT NULL,
                    detector_version TEXT NOT NULL,
                    config_hash TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    reused_from_job_id INTEGER REFERENCES analysis_jobs(id),
                    result_json TEXT NOT NULL DEFAULT '{}',
                    error_message TEXT NOT NULL DEFAULT '',
                    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_cache
                ON analysis_jobs(
                    revision_id, detector_key, detector_version, config_hash, status
                );

                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    asset_id INTEGER NOT NULL REFERENCES assets(id),
                    detector_key TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    remediation TEXT NOT NULL,
                    location TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'open',
                    first_seen_run_id INTEGER NOT NULL REFERENCES scan_runs(id),
                    last_seen_run_id INTEGER NOT NULL REFERENCES scan_runs(id),
                    resolved_run_id INTEGER REFERENCES scan_runs(id),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(project_id, asset_id, detector_key, fingerprint)
                );

                CREATE TABLE IF NOT EXISTS job_findings (
                    job_id INTEGER NOT NULL REFERENCES analysis_jobs(id),
                    finding_id INTEGER NOT NULL REFERENCES findings(id),
                    PRIMARY KEY(job_id, finding_id)
                );

                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_finding_id INTEGER NOT NULL UNIQUE REFERENCES findings(id),
                    detector_key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    remediation TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    approved_at TEXT
                );

                INSERT INTO schema_meta(key, value)
                VALUES ('schema_version', '1')
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;
                """
            )

    def create_or_get_project(self, root_url: str, name: str = "") -> dict[str, Any]:
        canonical = canonicalize_url(root_url)
        project_name = name.strip() or hostname(canonical)
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO projects(name, root_url, scope_host)
                VALUES (?, ?, ?)
                ON CONFLICT(root_url) DO UPDATE SET
                    name = CASE
                        WHEN excluded.name <> '' THEN excluded.name
                        ELSE projects.name
                    END,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (project_name, canonical, hostname(canonical)),
            )
            row = connection.execute(
                "SELECT * FROM projects WHERE root_url = ?", (canonical,)
            ).fetchone()
            return dict(row)

    def get_project(self, project_id: int) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_projects(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    p.*,
                    COUNT(DISTINCT a.id) AS asset_count,
                    COUNT(DISTINCT CASE WHEN f.status = 'open' THEN f.id END)
                        AS open_finding_count,
                    MAX(sr.started_at) AS last_scan_at
                FROM projects p
                LEFT JOIN assets a ON a.project_id = p.id
                LEFT JOIN findings f ON f.project_id = p.id
                LEFT JOIN scan_runs sr ON sr.project_id = p.id
                GROUP BY p.id
                ORDER BY COALESCE(MAX(sr.started_at), p.created_at) DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def create_run(self, project_id: int, root_url: str) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO scan_runs(project_id, root_url) VALUES (?, ?)",
                (project_id, root_url),
            )
            return int(cursor.lastrowid)

    def finish_run(
        self,
        run_id: int,
        status: str,
        summary: dict[str, Any],
        error_message: str = "",
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE scan_runs
                SET status = ?, summary_json = ?, error_message = ?,
                    finished_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, _json(summary), error_message, run_id),
            )

    def list_runs(self, project_id: int, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM scan_runs
                WHERE project_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (project_id, limit),
            ).fetchall()
            return [self._decode_row(row, "summary_json") for row in rows]

    def upsert_asset(
        self,
        project_id: int,
        url: str,
        kind: str,
        state: str = "discovered",
    ) -> dict[str, Any]:
        canonical = canonicalize_url(url)
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO assets(project_id, canonical_url, kind, state)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(project_id, canonical_url) DO UPDATE SET
                    kind = CASE
                        WHEN assets.kind IN ('endpoint', 'unknown')
                            AND excluded.kind NOT IN ('endpoint', 'unknown')
                        THEN excluded.kind
                        ELSE assets.kind
                    END,
                    state = CASE
                        WHEN excluded.state = 'fetched' THEN 'fetched'
                        ELSE assets.state
                    END,
                    last_seen_at = CURRENT_TIMESTAMP
                """,
                (project_id, canonical, kind, state),
            )
            row = connection.execute(
                """
                SELECT * FROM assets
                WHERE project_id = ? AND canonical_url = ?
                """,
                (project_id, canonical),
            ).fetchone()
            return dict(row)

    def mark_asset_error(self, asset_id: int, error_message: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE assets
                SET state = 'failed', fetch_error = ?,
                    last_checked_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (error_message[:1000], asset_id),
            )

    def record_standalone_finding(
        self,
        run_id: int,
        project_id: int,
        asset_id: int,
        detector_key: str,
        finding: FindingDraft,
    ) -> int:
        fingerprint = _sha256(f"{detector_key}\0{finding.dedupe_key}")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO findings(
                    project_id, asset_id, detector_key, fingerprint,
                    title, category, severity, confidence, evidence,
                    remediation, location, first_seen_run_id, last_seen_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, asset_id, detector_key, fingerprint)
                DO UPDATE SET
                    title = excluded.title,
                    category = excluded.category,
                    severity = excluded.severity,
                    confidence = excluded.confidence,
                    evidence = excluded.evidence,
                    remediation = excluded.remediation,
                    location = excluded.location,
                    status = 'open',
                    last_seen_run_id = excluded.last_seen_run_id,
                    resolved_run_id = NULL,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    project_id,
                    asset_id,
                    detector_key,
                    fingerprint,
                    finding.title,
                    finding.category,
                    finding.severity,
                    finding.confidence,
                    finding.evidence,
                    finding.remediation,
                    finding.location,
                    run_id,
                    run_id,
                ),
            )
            row = connection.execute(
                """
                SELECT id FROM findings
                WHERE project_id = ? AND asset_id = ?
                  AND detector_key = ? AND fingerprint = ?
                """,
                (project_id, asset_id, detector_key, fingerprint),
            ).fetchone()
            return int(row["id"])

    def resolve_standalone_findings(
        self,
        run_id: int,
        project_id: int,
        asset_id: int,
        detector_key: str,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE findings
                SET status = 'resolved', resolved_run_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ? AND asset_id = ?
                  AND detector_key = ? AND status = 'open'
                """,
                (run_id, project_id, asset_id, detector_key),
            )

    def latest_revision(self, asset_id: int) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM asset_revisions
                WHERE asset_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (asset_id,),
            ).fetchone()
            return self._decode_row(row, "headers_json", "redirect_chain_json") if row else None

    def save_revision(
        self,
        asset: dict[str, Any],
        fetch: FetchResult,
        kind: str,
    ) -> tuple[dict[str, Any], bool]:
        content_sha256 = _sha256(fetch.body)
        fingerprint_payload = {
            "content_sha256": content_sha256,
            "final_url": fetch.final_url,
            "headers": fetch.headers,
            "status_code": fetch.status_code,
        }
        fingerprint = _sha256(_json(fingerprint_payload))
        body_path = self._store_blob(content_sha256, fetch.body)

        with self.connect() as connection:
            existing = connection.execute(
                """
                SELECT * FROM asset_revisions
                WHERE asset_id = ? AND fingerprint_sha256 = ?
                """,
                (asset["id"], fingerprint),
            ).fetchone()
            created = existing is None
            if existing:
                connection.execute(
                    """
                    UPDATE asset_revisions
                    SET last_confirmed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (existing["id"],),
                )
                revision_id = existing["id"]
            else:
                cursor = connection.execute(
                    """
                    INSERT INTO asset_revisions(
                        asset_id, fingerprint_sha256, content_sha256, body_path,
                        final_url, status_code, headers_json, redirect_chain_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset["id"],
                        fingerprint,
                        content_sha256,
                        str(body_path),
                        fetch.final_url,
                        fetch.status_code,
                        _json(fetch.headers),
                        _json(fetch.redirect_chain),
                    ),
                )
                revision_id = cursor.lastrowid
            connection.execute(
                """
                UPDATE assets
                SET kind = ?, state = 'fetched', fetch_error = '',
                    last_checked_at = CURRENT_TIMESTAMP,
                    last_seen_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (kind, asset["id"]),
            )
            row = connection.execute(
                "SELECT * FROM asset_revisions WHERE id = ?", (revision_id,)
            ).fetchone()
            return (
                self._decode_row(row, "headers_json", "redirect_chain_json"),
                created,
            )

    def confirm_revision(self, asset_id: int, revision_id: int) -> dict[str, Any]:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE asset_revisions
                SET last_confirmed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (revision_id,),
            )
            connection.execute(
                """
                UPDATE assets
                SET state = 'fetched', fetch_error = '',
                    last_checked_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (asset_id,),
            )
            row = connection.execute(
                "SELECT * FROM asset_revisions WHERE id = ?", (revision_id,)
            ).fetchone()
            return self._decode_row(row, "headers_json", "redirect_chain_json")

    def load_snapshot(
        self,
        project_id: int,
        asset: dict[str, Any],
        revision: dict[str, Any],
    ) -> AssetSnapshot:
        body_path = Path(revision["body_path"])
        body = body_path.read_bytes()
        return AssetSnapshot(
            project_id=project_id,
            asset_id=asset["id"],
            revision_id=revision["id"],
            kind=asset["kind"],
            url=asset["canonical_url"],
            final_url=revision["final_url"],
            status_code=revision["status_code"],
            headers=revision["headers_json"],
            content_sha256=revision["content_sha256"],
            fingerprint_sha256=revision["fingerprint_sha256"],
            body=body,
        )

    def add_edge(
        self,
        project_id: int,
        source_asset_id: int,
        target_asset_id: int,
        relation: str,
        run_id: int,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO asset_edges(
                    project_id, source_asset_id, target_asset_id, relation,
                    first_seen_run_id, last_seen_run_id
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, source_asset_id, target_asset_id, relation)
                DO UPDATE SET last_seen_run_id = excluded.last_seen_run_id
                """,
                (
                    project_id,
                    source_asset_id,
                    target_asset_id,
                    relation,
                    run_id,
                    run_id,
                ),
            )

    def find_cached_job(
        self,
        revision_id: int,
        detector_key: str,
        detector_version: str,
        config_hash: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM analysis_jobs
                WHERE revision_id = ?
                  AND detector_key = ?
                  AND detector_version = ?
                  AND config_hash = ?
                  AND status IN ('completed', 'reused')
                ORDER BY
                    CASE status WHEN 'completed' THEN 0 ELSE 1 END,
                    id DESC
                LIMIT 1
                """,
                (revision_id, detector_key, detector_version, config_hash),
            ).fetchone()
            return self._decode_row(row, "result_json") if row else None

    def start_job(
        self,
        run_id: int,
        project_id: int,
        asset_id: int,
        revision_id: int,
        detector_key: str,
        detector_version: str,
        config_hash: str,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO analysis_jobs(
                    run_id, project_id, asset_id, revision_id,
                    detector_key, detector_version, config_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    project_id,
                    asset_id,
                    revision_id,
                    detector_key,
                    detector_version,
                    config_hash,
                ),
            )
            return int(cursor.lastrowid)

    def complete_job(
        self,
        job_id: int,
        run_id: int,
        project_id: int,
        asset_id: int,
        detector_key: str,
        result: dict[str, Any],
        findings: list[FindingDraft],
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE analysis_jobs
                SET status = 'completed', result_json = ?,
                    finished_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (_json(result), job_id),
            )
            seen_fingerprints: list[str] = []
            for finding in findings:
                fingerprint = _sha256(
                    f"{detector_key}\0{finding.dedupe_key}"
                )
                seen_fingerprints.append(fingerprint)
                connection.execute(
                    """
                    INSERT INTO findings(
                        project_id, asset_id, detector_key, fingerprint,
                        title, category, severity, confidence, evidence,
                        remediation, location, first_seen_run_id, last_seen_run_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, asset_id, detector_key, fingerprint)
                    DO UPDATE SET
                        title = excluded.title,
                        category = excluded.category,
                        severity = excluded.severity,
                        confidence = excluded.confidence,
                        evidence = excluded.evidence,
                        remediation = excluded.remediation,
                        location = excluded.location,
                        status = 'open',
                        last_seen_run_id = excluded.last_seen_run_id,
                        resolved_run_id = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        project_id,
                        asset_id,
                        detector_key,
                        fingerprint,
                        finding.title,
                        finding.category,
                        finding.severity,
                        finding.confidence,
                        finding.evidence,
                        finding.remediation,
                        finding.location,
                        run_id,
                        run_id,
                    ),
                )
                row = connection.execute(
                    """
                    SELECT id FROM findings
                    WHERE project_id = ? AND asset_id = ?
                      AND detector_key = ? AND fingerprint = ?
                    """,
                    (project_id, asset_id, detector_key, fingerprint),
                ).fetchone()
                connection.execute(
                    "INSERT OR IGNORE INTO job_findings(job_id, finding_id) VALUES (?, ?)",
                    (job_id, row["id"]),
                )

            parameters: list[Any] = [run_id, project_id, asset_id, detector_key]
            not_seen_clause = ""
            if seen_fingerprints:
                placeholders = ",".join("?" for _ in seen_fingerprints)
                not_seen_clause = f"AND fingerprint NOT IN ({placeholders})"
                parameters.extend(seen_fingerprints)
            connection.execute(
                f"""
                UPDATE findings
                SET status = 'resolved', resolved_run_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ? AND asset_id = ? AND detector_key = ?
                  AND status = 'open'
                  {not_seen_clause}
                """,
                parameters,
            )

    def reuse_job(
        self,
        run_id: int,
        project_id: int,
        asset_id: int,
        revision_id: int,
        detector_key: str,
        detector_version: str,
        config_hash: str,
        source_job: dict[str, Any],
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO analysis_jobs(
                    run_id, project_id, asset_id, revision_id,
                    detector_key, detector_version, config_hash, status,
                    reused_from_job_id, result_json, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'reused', ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    run_id,
                    project_id,
                    asset_id,
                    revision_id,
                    detector_key,
                    detector_version,
                    config_hash,
                    source_job["id"],
                    _json(source_job["result_json"]),
                ),
            )
            job_id = int(cursor.lastrowid)
            finding_rows = connection.execute(
                "SELECT finding_id FROM job_findings WHERE job_id = ?",
                (source_job["id"],),
            ).fetchall()
            for row in finding_rows:
                connection.execute(
                    "INSERT INTO job_findings(job_id, finding_id) VALUES (?, ?)",
                    (job_id, row["finding_id"]),
                )
                connection.execute(
                    """
                    UPDATE findings
                    SET status = 'open', last_seen_run_id = ?,
                        resolved_run_id = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (run_id, row["finding_id"]),
                )
            return job_id

    def fail_job(self, job_id: int, error_message: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE analysis_jobs
                SET status = 'failed', error_message = ?,
                    finished_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (error_message[:1000], job_id),
            )

    def list_assets(self, project_id: int) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    a.*,
                    ar.id AS revision_id,
                    ar.content_sha256,
                    ar.status_code,
                    ar.final_url,
                    ar.last_confirmed_at
                FROM assets a
                LEFT JOIN asset_revisions ar
                  ON ar.id = (
                    SELECT id FROM asset_revisions
                    WHERE asset_id = a.id
                    ORDER BY id DESC LIMIT 1
                  )
                WHERE a.project_id = ?
                ORDER BY
                    CASE a.kind
                        WHEN 'page' THEN 0
                        WHEN 'javascript' THEN 1
                        ELSE 2
                    END,
                    a.id
                """,
                (project_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_findings(
        self, project_id: int, include_resolved: bool = False
    ) -> list[dict[str, Any]]:
        status_clause = "" if include_resolved else "AND f.status = 'open'"
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT f.*, a.canonical_url AS asset_url, a.kind AS asset_kind
                FROM findings f
                JOIN assets a ON a.id = f.asset_id
                WHERE f.project_id = ? {status_clause}
                ORDER BY
                    CASE f.severity
                        WHEN 'critical' THEN 0
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                        ELSE 4
                    END,
                    f.id DESC
                """,
                (project_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_analysis_jobs(
        self, project_id: int, limit: int = 200
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    j.id,
                    j.run_id,
                    j.detector_key,
                    j.detector_version,
                    j.status,
                    j.reused_from_job_id,
                    j.error_message,
                    j.started_at,
                    j.finished_at,
                    a.id AS asset_id,
                    a.canonical_url AS asset_url,
                    a.kind AS asset_kind,
                    r.fingerprint_sha256 AS revision_fingerprint
                FROM analysis_jobs j
                JOIN assets a ON a.id = j.asset_id
                JOIN asset_revisions r ON r.id = j.revision_id
                WHERE j.project_id = ?
                ORDER BY j.id DESC
                LIMIT ?
                """,
                (project_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_asset_edges(self, project_id: int) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    e.id,
                    e.source_asset_id,
                    source.canonical_url AS source_url,
                    e.target_asset_id,
                    target.canonical_url AS target_url,
                    e.relation,
                    e.first_seen_run_id,
                    e.last_seen_run_id
                FROM asset_edges e
                JOIN assets source ON source.id = e.source_asset_id
                JOIN assets target ON target.id = e.target_asset_id
                WHERE e.project_id = ?
                ORDER BY e.id
                """,
                (project_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def project_detail(self, project_id: int) -> dict[str, Any] | None:
        project = self.get_project(project_id)
        if not project:
            return None
        assets = self.list_assets(project_id)
        findings = self.list_findings(project_id)
        runs = self.list_runs(project_id)
        jobs = self.list_analysis_jobs(project_id)
        edges = self.list_asset_edges(project_id)
        return {
            "project": project,
            "assets": assets,
            "findings": findings,
            "runs": runs,
            "jobs": jobs,
            "edges": edges,
            "stats": {
                "assets": len(assets),
                "pages": sum(item["kind"] == "page" for item in assets),
                "javascript": sum(
                    item["kind"] == "javascript" for item in assets
                ),
                "open_findings": len(findings),
                "runs": len(runs),
                "analysis_jobs": len(jobs),
                "asset_relations": len(edges),
            },
        }

    def promote_finding(self, finding_id: int) -> dict[str, Any]:
        with self.connect() as connection:
            finding = connection.execute(
                "SELECT * FROM findings WHERE id = ?", (finding_id,)
            ).fetchone()
            if not finding:
                raise KeyError(f"Finding {finding_id} does not exist")
            connection.execute(
                """
                INSERT INTO knowledge_items(
                    source_finding_id, detector_key, title, category,
                    signature, remediation
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_finding_id) DO NOTHING
                """,
                (
                    finding_id,
                    finding["detector_key"],
                    finding["title"],
                    finding["category"],
                    finding["fingerprint"],
                    finding["remediation"],
                ),
            )
            row = connection.execute(
                "SELECT * FROM knowledge_items WHERE source_finding_id = ?",
                (finding_id,),
            ).fetchone()
            return dict(row)

    def approve_knowledge(self, knowledge_id: int) -> dict[str, Any]:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE knowledge_items
                SET status = 'approved', approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (knowledge_id,),
            )
            row = connection.execute(
                "SELECT * FROM knowledge_items WHERE id = ?", (knowledge_id,)
            ).fetchone()
            if not row:
                raise KeyError(f"Knowledge item {knowledge_id} does not exist")
            return dict(row)

    def list_knowledge(self, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM knowledge_items"
        parameters: tuple[Any, ...] = ()
        if status:
            query += " WHERE status = ?"
            parameters = (status,)
        query += " ORDER BY id"
        with self.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
            return [dict(row) for row in rows]

    def _store_blob(self, content_sha256: str, body: bytes) -> Path:
        folder = self.settings.blob_dir / content_sha256[:2]
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / content_sha256
        if not path.exists():
            path.write_bytes(body)
        return path

    @staticmethod
    def _decode_row(
        row: sqlite3.Row, *json_fields: str
    ) -> dict[str, Any]:
        result = dict(row)
        for field in json_fields:
            result[field] = json.loads(result[field])
        return result
