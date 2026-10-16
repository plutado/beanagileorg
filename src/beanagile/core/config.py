"""Per-app settings. Data lives outside the repo, under ~/.beanagile/<app> by default."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    app: str
    title: str
    port: int
    host: str = "127.0.0.1"
    data_dir: Path | None = None
    odysseus_url: str | None = None
    odysseus_token: str | None = None
    session_days: int = 7

    def __post_init__(self) -> None:
        if self.data_dir is None:
            root = Path(os.environ.get("BEANAGILE_DATA", Path.home() / ".beanagile"))
            self.data_dir = root / self.app
        self.data_dir = Path(self.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.odysseus_url is None:
            self.odysseus_url = os.environ.get("BEANAGILE_ODYSSEUS_URL") or None
        if self.odysseus_token is None:
            self.odysseus_token = os.environ.get("BEANAGILE_ODYSSEUS_TOKEN") or None

    @property
    def db_path(self) -> Path:
        return self.data_dir / f"{self.app}.db"
