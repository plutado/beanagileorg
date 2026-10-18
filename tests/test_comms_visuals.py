import base64
import io
import json
import struct
import zlib

import pytest
from fastapi.testclient import TestClient

from beanagileorg.comms import visuals
from beanagileorg.comms.app import build
from beanagileorg.core.config import Settings

PASSWORD = "[placeholder-password]"


def tiny_png() -> bytes:
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    raw = b"\x00\xff\x00\x00"
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


@pytest.fixture(autouse=True)
def _no_release(monkeypatch):
    from beanagileorg.core import ask as _a
    monkeypatch.setattr(_a, "release", lambda s: None)  # never unload the real local Ollama during tests


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="comms", title="Comms", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def test_generate_image_files_it_as_generated(client, monkeypatch):
    seen = {}

    def fake(url, headers, body, timeout=180):
        seen.update(url=url, body=body)
        return {"data": [{"b64_json": base64.b64encode(tiny_png()).decode()}]}

    monkeypatch.setattr(visuals, "_post_json", fake)
    m = client.post("/api/media/generate", json={"prompt": "[A calm team planning]", "size": "square"}).json()
    assert m["source"] == "generated" and m["kind"] == "image" and m["details"]["prompt"] == "[A calm team planning]"
    assert seen["url"] == "http://127.0.0.1:8710/v1/images/generations" and seen["body"]["width"] == 1024 and seen["body"]["model"] == "flux2-klein-4b"
    assert "no text" in seen["body"]["prompt"]  # the house style rides along
    assert client.get(f"/api/media/{m['id']}/file").content.startswith(b"\x89PNG")
    client.put("/api/images/settings", json={"style": "[house style]", "model": "flux2-klein-9b"})
    client.post("/api/media/generate", json={"prompt": "[x]", "use_style": False})
    assert seen["body"]["prompt"] == "[x]" and seen["body"]["model"] == "flux2-klein-9b"
    assert client.post("/api/media/generate", json={"prompt": ""}).status_code == 400


def test_infographic_validation_save_and_png(client):
    bad = client.post("/api/infographics/save", json={"spec": {"template": "stats", "title": "[T]", "items": [{"value": "1", "label": "a"}]}})
    assert bad.status_code == 400  # stats need 2 to 4 items
    assert client.post("/api/infographics/save", json={"spec": {"template": "bars", "title": "[T]", "items": [{"label": "a", "value": "x"}, {"label": "b", "value": 2}]}}).status_code == 400
    g = client.post("/api/infographics/save", json={"spec": {"template": "progress", "title": "[We're three-quarters done]", "done": 18, "total": 24, "unit": "points"}}).json()
    assert g["spec"]["done"] == 18 and g["template"] == "progress"
    png = "data:image/png;base64," + base64.b64encode(tiny_png()).decode()
    r = client.post(f"/api/infographics/{g['id']}/png", json={"png": png}).json()
    media = client.get(f"/api/media/{r['media_id']}").json()
    assert media["source"] == "generated" and media["details"]["infographic_id"] == g["id"]
    assert client.get(f"/api/infographics/{g['id']}").json()["media_id"] == r["media_id"]
    assert client.post(f"/api/infographics/{g['id']}/png", json={"png": "data:image/png;base64," + base64.b64encode(b"not a png").decode()}).status_code == 400


def test_draft_uses_the_model_and_is_checked(client, monkeypatch):
    calls = []

    def fake_complete(s, key, system, user, max_tokens=1500):
        calls.append((system, user))
        return 'Here you go: {"template":"stats","title":"We finished 8 of 10 stories","items":[{"value":"8 of 10","label":"stories done"},{"value":"[Placeholder]","label":"points"}],"note":"[Source]"}'

    monkeypatch.setattr(visuals, "complete", fake_complete)
    r = client.post("/api/infographics/draft", json={"request": "Sprint progress for leadership"}).json()
    assert r["spec"]["template"] == "stats" and r["spec"]["items"][0]["value"] == "8 of 10"
    assert "Use only numbers and names that appear in the facts" in calls[0][0] and "(none given)" in calls[0][1]
    monkeypatch.setattr(visuals, "complete", lambda *a, **k: "no json here")
    assert client.post("/api/infographics/draft", json={"request": "x"}).status_code == 502
    assert client.post("/api/infographics/draft", json={"request": "x", "facts": "weekly"}).status_code == 400  # toolkit not connected
    assert client.get("/api/ask/settings").json()["model"] == "qwen3.6:35b-a3b"
