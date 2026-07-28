from __future__ import annotations

from typing import Protocol

from assettrace.models import AssetSnapshot, DetectorResult


class Detector(Protocol):
    key: str
    version: str
    supported_kinds: frozenset[str]

    def analyze(self, snapshot: AssetSnapshot) -> DetectorResult:
        ...
