"""Per-app settings. Data lives outside the repo, under ~/.beanagileorg/<app> by default."""

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
    allowed_hosts: frozenset = frozenset()

    def __post_init__(self) -> None:
        if self.data_dir is None:
            root = Path(os.environ.get("BEANAGILEORG_DATA", Path.home() / ".beanagileorg"))
            self.data_dir = root / self.app
        self.data_dir = Path(self.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.odysseus_url is None:
            self.odysseus_url = os.environ.get("BEANAGILEORG_ODYSSEUS_URL") or None
        # Requests must name this machine or this app's local domain; anything else is refused (DNS rebinding).
        extra = {h.strip().lower() for h in os.environ.get("BEANAGILEORG_ALLOWED_HOSTS", "").split(",") if h.strip()}
        self.allowed_hosts = frozenset({"127.0.0.1", "localhost", "::1", f"{self.app}.beanagile.org", "testserver"} | extra | set(self.allowed_hosts))
        if self.odysseus_token is None:
            self.odysseus_token = os.environ.get("BEANAGILEORG_ODYSSEUS_TOKEN") or None

    @property
    def db_path(self) -> Path:
        return self.data_dir / f"{self.app}.db"
