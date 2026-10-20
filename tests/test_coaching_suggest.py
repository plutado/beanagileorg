"""Coaching suggested from what's happening, the weekly prompt, reflections linked to guides, detail-page tips."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core import coaching as starter
from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def c(tmp_path):
    client = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    client.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return client


def test_suggestions_follow_signals(c):
    assert c.get("/api/coaching/suggestions").json()["suggestions"] == []
    rid = c.post("/api/retros", json={"date": "2026-10-01", "format": "start / stop / continue"}).json()["id"]
    c.post("/api/retro-commitments", json={"retro_id": rid, "commitment": "[Shorter standups]", "due": (date.today() - timedelta(days=3)).isoformat()})
    c.post("/api/risks", json={"title": "[Release window]", "level": "high"})
    for i in range(3):
        c.post("/api/reflections", json={"date": (date.today() - timedelta(days=i * 5)).isoformat(), "entry": "[Tired]", "energy": 2})
    s = c.get("/api/coaching/suggestions").json()
    slugs = [x["slug"] for x in s["suggestions"]]
    assert slugs[:3] == ["retros", "honest-status", "transition-traps"] and len(slugs) <= 4
    assert s["prompt"]


def test_reflection_linked_to_guide(c):
    c.post("/api/reflections", json={"date": date.today().isoformat(), "entry": "[On saying no]", "guide_slug": "personal-disciplines"})
    g = c.get("/api/coaching/guide/personal-disciplines").json()
    assert g["reflections"][0]["entry"] == "[On saying no]"


def test_detail_tips_are_served(c):
    tips = c.get("/api/coaching/tips").json()
    assert tips["/retros/*"][0]["guide"] == "retros" and "/onboarding/*" in tips
    assert all(r.endswith("/*") or r.startswith("/") for r in starter.TIPS)
