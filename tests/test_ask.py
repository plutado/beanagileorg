import json
import os

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core import ask as ask_mod
from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture(autouse=True)
def _no_release(monkeypatch):
    from beanagileorg.core import ask as _a
    monkeypatch.setattr(_a, "release", lambda s: None)  # never unload the real local Ollama during tests


@pytest.fixture
def setup(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    ask_mod._INDEX_CACHE.clear()
    return c, tmp_path


class FakeModel:
    """Plays an OpenAI-compatible model: first asks to search, then answers from what the tool returned."""

    def __init__(self):
        self.seen = []

    def __call__(self, url, headers, body, timeout=180):
        self.seen.append((url, headers, body))
        msgs = body["messages"]
        if msgs[-1]["role"] != "tool":
            return {"choices": [{"message": {"content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "search", "arguments": json.dumps({"query": "sandbox"})}}]}}]}
        found = json.loads(msgs[-1]["content"])
        cites = " ".join(f"[{r['entity']}:{r['id']}]" for r in found)
        return {"choices": [{"message": {"content": f"<think>hmm</think>Found {len(found)}. {cites}"}}]}


def test_ask_uses_tools_and_cites(setup, monkeypatch):
    c, _ = setup
    a = c.post("/api/actions", json={"concern": "[Automate sandbox refreshes?]", "notes": "[Private sandbox note]"}).json()["id"]
    fake = FakeModel()
    monkeypatch.setattr(ask_mod, "_post_json", fake)
    r = c.post("/api/ask", json={"question": "What about sandboxes?"}).json()
    assert r["answer"].startswith("Found 1.") and "<think>" not in r["answer"]
    assert r["citations"] == [{"entity": "action_item", "id": a, "title": "[Automate sandbox refreshes?]", "path": f"/dev-sync/{a}"}]
    assert r["tools_used"][0]["tool"] == "search" and r["local"] and r["floor"] == "private"
    url, headers, body = fake.seen[0]
    assert url == "http://127.0.0.1:11434/v1/chat/completions" and "Authorization" not in headers
    assert {t["function"]["name"] for t in body["tools"]} >= {"search", "get_record", "list_records", "today", "weekly_report"}
    assert "Private sandbox note" in fake.seen[1][2]["messages"][-1]["content"]  # local model, private viewer: sees notes
    assert c.post("/api/ask", json={"question": ""}).status_code == 400


def test_presentation_and_cloud_limit_what_the_model_sees(setup, monkeypatch):
    c, tmp = setup
    c.post("/api/actions", json={"concern": "[Automate sandbox refreshes?]", "notes": "[Private sandbox note]"})
    c.post("/api/roadmap", json={"title": "[Sandbox roadmap milestone]"})
    fake = FakeModel()
    monkeypatch.setattr(ask_mod, "_post_json", fake)
    # a cloud provider: exportable data only, key kept in a private file and never echoed
    s = c.put("/api/ask/settings", json={"provider": "openai", "base_url": "https://api.example.com/v1", "model": "[cloud-model]", "api_key": "[test-key]"}).json()
    assert s["has_key"] and not s["local"] and "api_key" not in s
    key_file = tmp / "ask-secret.json"
    assert json.loads(key_file.read_text())["api_key"] == "[test-key]" and oct(os.stat(key_file).st_mode & 0o777) == "0o600"
    r = c.post("/api/ask", json={"question": "sandbox?"}).json()
    assert r["floor"] == "exportable" and not r["local"]
    assert fake.seen[0][1]["Authorization"] == "Bearer [test-key]"
    tool_out = fake.seen[1][2]["messages"][-1]["content"]
    assert "Sandbox roadmap milestone" in tool_out and "Private sandbox note" not in tool_out and "Automate sandbox" not in tool_out
    assert any(e["kind"] == "ask:cloud" for e in c.get("/api/exports").json())
    # allowing private data to the cloud lifts the limit
    c.put("/api/ask/settings", json={"allow_private_cloud": True})
    assert c.post("/api/ask", json={"question": "sandbox?"}).json()["floor"] == "private"
    # presentation mode: presentable only, whatever the provider
    c.put("/api/ask/settings", json={"base_url": "http://127.0.0.1:11434/v1", "allow_private_cloud": False, "api_key": ""})
    assert not key_file.exists()
    c.post("/api/session/presentation", json={"on": True})
    r = c.post("/api/ask", json={"question": "sandbox?"}).json()
    assert r["floor"] == "presentable" and "Private sandbox note" not in fake.seen[-1][2]["messages"][-1]["content"]
    assert c.get("/api/ask/settings").status_code in (401, 403)


def test_anthropic_shape(setup, monkeypatch):
    c, _ = setup
    c.post("/api/actions", json={"concern": "[Automate sandbox refreshes?]"})
    calls = []

    def fake(url, headers, body, timeout=180):
        calls.append((url, headers, body))
        if len(calls) == 1:
            return {"content": [{"type": "tool_use", "id": "t1", "name": "search", "input": {"query": "sandbox"}}]}
        return {"content": [{"type": "text", "text": "One item. [action_item:1]"}]}

    monkeypatch.setattr(ask_mod, "_post_json", fake)
    c.put("/api/ask/settings", json={"provider": "anthropic", "base_url": "https://api.anthropic.com", "model": "claude-sonnet-5-5", "api_key": "[k]", "allow_private_cloud": True})
    r = c.post("/api/ask", json={"question": "sandbox?"}).json()
    assert r["answer"] == "One item. [action_item:1]" and r["citations"][0]["id"] == 1
    assert calls[0][0] == "https://api.anthropic.com/v1/messages" and calls[0][1]["x-api-key"] == "[k]"
    assert calls[1][2]["messages"][-1]["content"][0]["type"] == "tool_result"
    assert c.put("/api/ask/settings", json={"provider": "other"}).status_code == 400


def test_release_only_for_local_ollama(monkeypatch):
    from beanagileorg.core import ask as a
    import importlib
    real = importlib.reload(a).release  # the unpatched function
    calls = []
    monkeypatch.setattr(a.urllib.request, "urlopen", lambda req, timeout=10: calls.append((req.full_url, req.data)) or __import__("io").BytesIO(b""))
    real({**a.DEFAULTS})
    assert calls and calls[0][0] == "http://127.0.0.1:11434/api/generate" and b'"keep_alive": 0' in calls[0][1]
    calls.clear()
    real({**a.DEFAULTS, "release_after": False})
    real({**a.DEFAULTS, "base_url": "https://api.example.com/v1"})
    real({**a.DEFAULTS, "provider": "anthropic"})
    assert calls == []
