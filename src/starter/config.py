"""Settings read from the environment (`just` loads `.env` for you)."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    host: str = field(
        default_factory=lambda: os.environ.get("MOSAICO_HOST", "mosaico.hackathon.internal")
    )
    port: int = field(default_factory=lambda: int(os.environ.get("MOSAICO_PORT", "6726")))
    api_key: str | None = field(default_factory=lambda: os.environ.get("MOSAICO_API_KEY") or None)
    tls_cert: str | None = field(
        default_factory=lambda: os.environ.get("MOSAICO_TLS_CERT_FILE") or None
    )
    team: str = field(default_factory=lambda: os.environ.get("TEAM", ""))
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("DATA_DIR", "data")))


def get_settings() -> Settings:
    return Settings()
