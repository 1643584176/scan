from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class FetchResult:
    requested_url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    body: bytes
    not_modified: bool = False
    redirect_chain: tuple[str, ...] = ()


@dataclass(frozen=True)
class AssetSnapshot:
    project_id: int
    asset_id: int
    revision_id: int
    kind: str
    url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    content_sha256: str
    fingerprint_sha256: str
    body: bytes

    @property
    def text(self) -> str:
        content_type = self.headers.get("content-type", "").lower()
        encoding = "utf-8"
        if "charset=" in content_type:
            encoding = content_type.split("charset=", 1)[1].split(";", 1)[0].strip()
        try:
            return self.body.decode(encoding, errors="replace")
        except LookupError:
            return self.body.decode("utf-8", errors="replace")


@dataclass(frozen=True)
class Discovery:
    url: str
    kind: str
    relation: str
    fetch: bool = False


@dataclass(frozen=True)
class FindingDraft:
    dedupe_key: str
    title: str
    category: str
    severity: str
    confidence: str
    evidence: str
    remediation: str
    location: str = ""


@dataclass
class DetectorResult:
    findings: list[FindingDraft] = field(default_factory=list)
    discoveries: list[Discovery] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "findings": [asdict(item) for item in self.findings],
            "discoveries": [asdict(item) for item in self.discoveries],
            "facts": self.facts,
        }
