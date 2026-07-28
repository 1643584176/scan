from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import dataclass
from typing import Iterable

from assettrace.config import Settings
from assettrace.detectors import default_detectors
from assettrace.detectors.base import Detector
from assettrace.fetcher import HttpFetcher
from assettrace.models import DetectorResult, FindingDraft
from assettrace.storage import Repository
from assettrace.urls import InvalidUrl, canonicalize_url, is_host_in_scope


@dataclass(frozen=True)
class _QueuedAsset:
    url: str
    kind: str


class ScanEngine:
    def __init__(
        self,
        repository: Repository,
        settings: Settings,
        fetcher: HttpFetcher | None = None,
        detectors: Iterable[Detector] | None = None,
    ):
        self.repository = repository
        self.settings = settings
        self.fetcher = fetcher or HttpFetcher(settings)
        self.detectors = tuple(
            default_detectors() if detectors is None else detectors
        )
        self.config_hash = hashlib.sha256(
            json.dumps(
                {"engine_contract": 1},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    async def scan_url(self, url: str, name: str = "") -> dict:
        project = self.repository.create_or_get_project(url, name)
        return await self.scan_project(project["id"])

    async def scan_project(self, project_id: int) -> dict:
        project = self.repository.get_project(project_id)
        if not project:
            raise KeyError(f"Project {project_id} does not exist")

        run_id = self.repository.create_run(project_id, project["root_url"])
        summary = {
            "run_id": run_id,
            "fetched_assets": 0,
            "new_revisions": 0,
            "reused_revisions": 0,
            "analyzed_jobs": 0,
            "reused_jobs": 0,
            "failed_jobs": 0,
            "fetch_errors": 0,
            "discovered_assets": 0,
            "discovery_limit_hit": False,
        }
        queue = deque([_QueuedAsset(project["root_url"], "page")])
        queued_urls = {canonicalize_url(project["root_url"])}
        processed_urls: set[str] = set()
        root_failed = False

        try:
            while queue and len(processed_urls) < self.settings.max_assets_per_scan:
                queued = queue.popleft()
                canonical_url = canonicalize_url(queued.url)
                if canonical_url in processed_urls:
                    continue
                processed_urls.add(canonical_url)
                asset = self.repository.upsert_asset(
                    project_id, canonical_url, queued.kind
                )
                previous = self.repository.latest_revision(asset["id"])

                try:
                    fetch = await self.fetcher.fetch(canonical_url, previous)
                    if fetch.not_modified and previous:
                        revision = self.repository.confirm_revision(
                            asset["id"], previous["id"]
                        )
                        summary["reused_revisions"] += 1
                    else:
                        kind = self._infer_kind(
                            queued.kind,
                            fetch.headers.get("content-type", ""),
                            fetch.final_url,
                        )
                        revision, created = self.repository.save_revision(
                            asset, fetch, kind
                        )
                        asset["kind"] = kind
                        summary["new_revisions" if created else "reused_revisions"] += 1
                    self.repository.resolve_standalone_findings(
                        run_id,
                        project_id,
                        asset["id"],
                        "transport-tls",
                    )
                    summary["fetched_assets"] += 1
                except Exception as exc:
                    self.repository.mark_asset_error(asset["id"], str(exc))
                    transport_finding = self._transport_finding(
                        canonical_url, exc
                    )
                    if transport_finding:
                        self.repository.record_standalone_finding(
                            run_id,
                            project_id,
                            asset["id"],
                            "transport-tls",
                            transport_finding,
                        )
                    summary["fetch_errors"] += 1
                    if canonical_url == project["root_url"]:
                        root_failed = True
                    continue

                snapshot = self.repository.load_snapshot(
                    project_id, asset, revision
                )
                for detector in self.detectors:
                    if snapshot.kind not in detector.supported_kinds:
                        continue
                    result, reused = self._run_detector(
                        run_id, project_id, asset, snapshot, detector
                    )
                    summary["reused_jobs" if reused else "analyzed_jobs"] += 1
                    if result is None:
                        summary["failed_jobs"] += 1
                        continue

                    discoveries = sorted(
                        result.discoveries,
                        key=lambda item: not item.fetch,
                    )
                    for discovery in discoveries:
                        if (
                            summary["discovered_assets"]
                            >= self.settings.max_discoveries_per_scan
                        ):
                            summary["discovery_limit_hit"] = True
                            break
                        try:
                            target_url = canonicalize_url(
                                discovery.url, snapshot.final_url
                            )
                        except (InvalidUrl, ValueError):
                            continue
                        target = self.repository.upsert_asset(
                            project_id,
                            target_url,
                            discovery.kind,
                        )
                        self.repository.add_edge(
                            project_id,
                            asset["id"],
                            target["id"],
                            discovery.relation,
                            run_id,
                        )
                        summary["discovered_assets"] += 1
                        if (
                            discovery.fetch
                            and discovery.kind
                            in {"javascript", "source-map"}
                            and is_host_in_scope(
                                target_url, project["scope_host"]
                            )
                            and target_url not in queued_urls
                        ):
                            queue.append(
                                _QueuedAsset(target_url, discovery.kind)
                            )
                            queued_urls.add(target_url)

            status = "failed" if root_failed else "completed"
            self.repository.finish_run(run_id, status, summary)
        except Exception as exc:
            self.repository.finish_run(
                run_id, "failed", summary, error_message=str(exc)
            )
            raise

        detail = self.repository.project_detail(project_id)
        return {
            "run": {
                "id": run_id,
                "status": status,
                "summary": summary,
            },
            "project": detail,
        }

    def _run_detector(
        self,
        run_id: int,
        project_id: int,
        asset: dict,
        snapshot,
        detector: Detector,
    ) -> tuple[DetectorResult | None, bool]:
        cached = self.repository.find_cached_job(
            snapshot.revision_id,
            detector.key,
            detector.version,
            self.config_hash,
        )
        if cached:
            self.repository.reuse_job(
                run_id,
                project_id,
                asset["id"],
                snapshot.revision_id,
                detector.key,
                detector.version,
                self.config_hash,
                cached,
            )
            return self._result_from_dict(cached["result_json"]), True

        job_id = self.repository.start_job(
            run_id,
            project_id,
            asset["id"],
            snapshot.revision_id,
            detector.key,
            detector.version,
            self.config_hash,
        )
        try:
            result = detector.analyze(snapshot)
            self.repository.complete_job(
                job_id,
                run_id,
                project_id,
                asset["id"],
                detector.key,
                result.to_dict(),
                result.findings,
            )
            return result, False
        except Exception as exc:
            self.repository.fail_job(job_id, str(exc))
            return None, False

    @staticmethod
    def _infer_kind(requested_kind: str, content_type: str, url: str) -> str:
        lowered_type = content_type.lower()
        lowered_url = url.lower()
        if "javascript" in lowered_type or lowered_url.split("?", 1)[0].endswith(
            (".js", ".mjs")
        ):
            return "javascript"
        if "html" in lowered_type:
            return "page"
        return requested_kind

    @staticmethod
    def _result_from_dict(data: dict) -> DetectorResult:
        from assettrace.models import Discovery, FindingDraft

        return DetectorResult(
            findings=[FindingDraft(**item) for item in data.get("findings", [])],
            discoveries=[
                Discovery(**item) for item in data.get("discoveries", [])
            ],
            facts=data.get("facts", {}),
        )

    @staticmethod
    def _transport_finding(
        url: str, error: Exception
    ) -> FindingDraft | None:
        message = str(error)
        if (
            "CERTIFICATE_VERIFY_FAILED" not in message
            or "Hostname mismatch" not in message
        ):
            return None
        return FindingDraft(
            dedupe_key="certificate-hostname-mismatch",
            title="TLS certificate does not cover the requested hostname",
            category="transport-security",
            severity="low",
            confidence="high",
            evidence=(
                "A verified TLS connection failed because the certificate "
                "hostname does not match the requested domain."
            ),
            remediation=(
                "Configure the HTTPS virtual host and CDN certificate to "
                "include the requested domain in its Subject Alternative Names."
            ),
            location=url,
        )
