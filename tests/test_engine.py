from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from assettrace.config import Settings
from assettrace.engine import ScanEngine
from assettrace.knowledge import export_approved_knowledge
from assettrace.models import DetectorResult, FetchResult, FindingDraft
from assettrace.storage import Repository
from assettrace.urls import canonicalize_url


class FakeFetcher:
    def __init__(self, responses: dict[str, tuple]):
        self.responses = {
            canonicalize_url(url): value for url, value in responses.items()
        }
        self.calls: list[str] = []

    async def fetch(self, url: str, previous_revision: dict | None = None):
        canonical = canonicalize_url(url)
        self.calls.append(canonical)
        response = self.responses[canonical]
        status, headers, body = response[:3]
        final_url = (
            canonicalize_url(response[3]) if len(response) > 3 else canonical
        )
        if previous_revision:
            unchanged = (
                previous_revision["content_sha256"]
                == hashlib.sha256(body).hexdigest()
                and previous_revision["status_code"] == status
                and previous_revision["headers_json"] == headers
            )
            if unchanged:
                return FetchResult(
                    requested_url=canonical,
                    final_url=final_url,
                    status_code=status,
                    headers=headers,
                    body=b"",
                    not_modified=True,
                )
        return FetchResult(
            requested_url=canonical,
            final_url=final_url,
            status_code=status,
            headers=headers,
            body=body,
        )


class VersionedDetector:
    key = "versioned-check"
    supported_kinds = frozenset({"page"})

    def __init__(self, version: str):
        self.version = version

    def analyze(self, snapshot):
        return DetectorResult(
            findings=[
                FindingDraft(
                    dedupe_key="stable",
                    title="Versioned finding",
                    category="test",
                    severity="low",
                    confidence="high",
                    evidence="Sanitized evidence",
                    remediation="Use the fixed implementation.",
                )
            ]
        )


class MarkerDetector:
    key = "marker-check"
    version = "1.0.0"
    supported_kinds = frozenset({"page"})

    def analyze(self, snapshot):
        if "unsafe-marker" not in snapshot.text:
            return DetectorResult()
        return DetectorResult(
            findings=[
                FindingDraft(
                    dedupe_key="unsafe-marker",
                    title="Unsafe marker found",
                    category="test",
                    severity="medium",
                    confidence="high",
                    evidence="Marker is present.",
                    remediation="Remove the marker.",
                )
            ]
        )


class TlsMismatchFetcher:
    async def fetch(self, url: str, previous_revision: dict | None = None):
        raise RuntimeError(
            "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: "
            "Hostname mismatch, certificate is not valid for 'example.test'."
        )


class IncrementalScanTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.settings = Settings(
            database_path=root / "assettrace.db",
            blob_dir=root / "blobs",
            skill_dir=root / "skill",
            allow_private_targets=True,
        )
        self.repository = Repository(self.settings)

    def tearDown(self):
        self.temporary.cleanup()

    async def test_second_scan_reuses_unchanged_page_and_javascript(self):
        page_url = "https://example.test/"
        script_url = "https://example.test/app.js"
        fetcher = FakeFetcher(
            {
                page_url: (
                    200,
                    {"content-type": "text/html"},
                    b'<html><script src="/app.js"></script></html>',
                ),
                script_url: (
                    200,
                    {"content-type": "application/javascript"},
                    b'fetch("/api/users")',
                ),
            }
        )
        engine = ScanEngine(self.repository, self.settings, fetcher=fetcher)

        first = await engine.scan_url(page_url)
        second = await engine.scan_url(page_url)

        self.assertEqual(first["run"]["summary"]["analyzed_jobs"], 3)
        self.assertEqual(first["run"]["summary"]["reused_jobs"], 0)
        self.assertEqual(second["run"]["summary"]["analyzed_jobs"], 0)
        self.assertEqual(second["run"]["summary"]["reused_jobs"], 3)
        self.assertEqual(second["run"]["summary"]["reused_revisions"], 2)

    async def test_only_changed_javascript_is_reanalyzed(self):
        page_url = "https://example.test/"
        script_url = "https://example.test/app.js"
        fetcher = FakeFetcher(
            {
                page_url: (
                    200,
                    {"content-type": "text/html"},
                    b'<script src="/app.js"></script>',
                ),
                script_url: (
                    200,
                    {"content-type": "application/javascript"},
                    b'fetch("/api/v1")',
                ),
            }
        )
        engine = ScanEngine(self.repository, self.settings, fetcher=fetcher)
        await engine.scan_url(page_url)
        fetcher.responses[canonicalize_url(script_url)] = (
            200,
            {"content-type": "application/javascript"},
            b'fetch("/api/v2")',
        )

        second = await engine.scan_url(page_url)

        self.assertEqual(second["run"]["summary"]["analyzed_jobs"], 1)
        self.assertEqual(second["run"]["summary"]["reused_jobs"], 2)
        self.assertEqual(second["run"]["summary"]["new_revisions"], 1)

    async def test_root_domain_scan_fetches_javascript_from_www_subdomain(self):
        page_url = "https://example.test/"
        final_url = "https://www.example.test/home"
        script_url = "https://www.example.test/app.js"
        fetcher = FakeFetcher(
            {
                page_url: (
                    200,
                    {"content-type": "text/html"},
                    b'<script src="/app.js"></script>',
                    final_url,
                ),
                script_url: (
                    200,
                    {"content-type": "application/javascript"},
                    b'fetch("/api/status")',
                ),
            }
        )
        engine = ScanEngine(self.repository, self.settings, fetcher=fetcher)

        result = await engine.scan_url(page_url)

        self.assertEqual(result["run"]["summary"]["fetched_assets"], 2)
        self.assertIn(canonicalize_url(script_url), fetcher.calls)

    async def test_referenced_source_map_is_fetched_and_analyzed(self):
        page_url = "https://example.test/"
        script_url = "https://example.test/app.js"
        map_url = "https://example.test/app.js.map"
        fetcher = FakeFetcher(
            {
                page_url: (
                    200,
                    {"content-type": "text/html"},
                    b'<script src="/app.js"></script>',
                ),
                script_url: (
                    200,
                    {"content-type": "application/javascript"},
                    b'console.log("ok");\\n//# sourceMappingURL=app.js.map',
                ),
                map_url: (
                    200,
                    {"content-type": "application/json"},
                    (
                        b'{"version":3,"sources":["src/app.js"],'
                        b'"sourcesContent":["export const ok = true;"],'
                        b'"names":[],"mappings":""}'
                    ),
                ),
            }
        )
        engine = ScanEngine(self.repository, self.settings, fetcher=fetcher)

        result = await engine.scan_url(page_url)
        project_id = result["project"]["project"]["id"]
        findings = self.repository.list_findings(project_id)

        self.assertEqual(result["run"]["summary"]["fetched_assets"], 3)
        self.assertTrue(
            any(
                item["category"] == "source-map-exposure"
                for item in findings
            )
        )

    async def test_detector_version_change_invalidates_analysis_cache(self):
        page_url = "https://example.test/"
        fetcher = FakeFetcher(
            {
                page_url: (
                    200,
                    {"content-type": "text/html"},
                    b"<html></html>",
                )
            }
        )
        first_engine = ScanEngine(
            self.repository,
            self.settings,
            fetcher=fetcher,
            detectors=(VersionedDetector("1.0.0"),),
        )
        project_result = await first_engine.scan_url(page_url)
        project_id = project_result["project"]["project"]["id"]
        second_engine = ScanEngine(
            self.repository,
            self.settings,
            fetcher=fetcher,
            detectors=(VersionedDetector("2.0.0"),),
        )

        second = await second_engine.scan_project(project_id)

        self.assertEqual(second["run"]["summary"]["analyzed_jobs"], 1)
        self.assertEqual(second["run"]["summary"]["reused_jobs"], 0)

    async def test_only_approved_sanitized_knowledge_is_exported(self):
        page_url = "https://secret-target.test/private"
        fetcher = FakeFetcher(
            {
                page_url: (
                    200,
                    {"content-type": "text/html"},
                    b"<html></html>",
                )
            }
        )
        engine = ScanEngine(
            self.repository,
            self.settings,
            fetcher=fetcher,
            detectors=(VersionedDetector("1.0.0"),),
        )
        result = await engine.scan_url(page_url)
        project_id = result["project"]["project"]["id"]
        finding = self.repository.list_findings(project_id)[0]
        knowledge = self.repository.promote_finding(finding["id"])

        draft_path = export_approved_knowledge(
            self.repository, self.settings.skill_dir
        )
        self.assertNotIn("Versioned finding", draft_path.read_text("utf-8"))

        self.repository.approve_knowledge(knowledge["id"])
        approved_path = export_approved_knowledge(
            self.repository, self.settings.skill_dir
        )
        content = approved_path.read_text("utf-8")
        self.assertIn("Versioned finding", content)
        self.assertNotIn("secret-target.test", content)
        self.assertNotIn("Sanitized evidence", content)

    async def test_finding_is_resolved_after_fresh_clean_revision(self):
        page_url = "https://example.test/"
        canonical = canonicalize_url(page_url)
        fetcher = FakeFetcher(
            {
                page_url: (
                    200,
                    {"content-type": "text/html"},
                    b"<html>unsafe-marker</html>",
                )
            }
        )
        engine = ScanEngine(
            self.repository,
            self.settings,
            fetcher=fetcher,
            detectors=(MarkerDetector(),),
        )
        first = await engine.scan_url(page_url)
        project_id = first["project"]["project"]["id"]
        self.assertEqual(len(self.repository.list_findings(project_id)), 1)

        fetcher.responses[canonical] = (
            200,
            {"content-type": "text/html"},
            b"<html>clean</html>",
        )
        await engine.scan_project(project_id)

        self.assertEqual(self.repository.list_findings(project_id), [])
        historical = self.repository.list_findings(
            project_id, include_resolved=True
        )
        self.assertEqual(historical[0]["status"], "resolved")

    async def test_tls_hostname_mismatch_becomes_security_finding(self):
        engine = ScanEngine(
            self.repository,
            self.settings,
            fetcher=TlsMismatchFetcher(),
            detectors=(),
        )

        result = await engine.scan_url("https://example.test/")
        project_id = result["project"]["project"]["id"]
        findings = self.repository.list_findings(project_id)

        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["detector_key"], "transport-tls")
        self.assertEqual(findings[0]["confidence"], "high")


if __name__ == "__main__":
    unittest.main()
