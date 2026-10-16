"""Optional link to an Odysseus hub. Every app must work when this is not configured."""

import json
import urllib.request


class OdysseusClient:
    def __init__(self, base_url: str | None, token: str | None) -> None:
        self.base_url = (base_url or "").rstrip("/") or None
        self.token = token

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.token)

    def status(self) -> str:
        return "configured" if self.configured else "not configured"

    def get(self, path: str, timeout: float = 5.0) -> dict:
        if not self.configured:
            raise RuntimeError("Odysseus is not configured; this feature is switched off.")
        request = urllib.request.Request(
            f"{self.base_url}{path}", headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode())
