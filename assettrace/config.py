from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_path: Path = BASE_DIR / "data" / "assettrace.db"
    blob_dir: Path = BASE_DIR / "data" / "blobs"
    skill_dir: Path = BASE_DIR / "skills" / "scan-ledger-research"
    request_timeout_seconds: float = 15.0
    max_body_bytes: int = 2 * 1024 * 1024
    max_assets_per_scan: int = 40
    max_discoveries_per_scan: int = 500
    allow_private_targets: bool = False
    user_agent: str = "AssetTrace/0.1 (+authorized-security-analysis)"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_path=Path(
                os.getenv("ASSETTRACE_DB", str(BASE_DIR / "data" / "assettrace.db"))
            ),
            blob_dir=Path(
                os.getenv("ASSETTRACE_BLOB_DIR", str(BASE_DIR / "data" / "blobs"))
            ),
            skill_dir=Path(
                os.getenv(
                    "ASSETTRACE_SKILL_DIR",
                    str(BASE_DIR / "skills" / "scan-ledger-research"),
                )
            ),
            request_timeout_seconds=float(
                os.getenv("ASSETTRACE_TIMEOUT_SECONDS", "15")
            ),
            max_body_bytes=int(
                os.getenv("ASSETTRACE_MAX_BODY_BYTES", str(2 * 1024 * 1024))
            ),
            max_assets_per_scan=int(
                os.getenv("ASSETTRACE_MAX_ASSETS", "40")
            ),
            max_discoveries_per_scan=int(
                os.getenv("ASSETTRACE_MAX_DISCOVERIES", "500")
            ),
            allow_private_targets=_env_bool("ASSETTRACE_ALLOW_PRIVATE_TARGETS"),
            user_agent=os.getenv(
                "ASSETTRACE_USER_AGENT",
                "AssetTrace/0.1 (+authorized-security-analysis)",
            ),
        )

    def ensure_directories(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.blob_dir.mkdir(parents=True, exist_ok=True)
