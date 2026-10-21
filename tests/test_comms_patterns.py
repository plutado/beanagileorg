"""Decks that learn from what you've presented before: outcomes, patterns per audience, and a deck started from one."""

import pytest
from fastapi.testclient import TestClient

from beanagileorg.comms.app import build
from beanagileorg.core.config import Settings

PASSWORD = "[placeholder-password]"
AUDIENCE = "[Placeholder leadership group]"


@pytest.fixture
def c(tmp_path):
    client = TestClient(build(Settings(app="comms", title="Comms", port=0, data_dir=tmp_path)), follow_redirects=False)
    client.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return client


def deck(c, title, layouts, status="presented", audience=AUDIENCE):
    d = c.post("/api/decks", json={"title": title, "audience": audience}).json()["id"]
    for i, layout in enumerate(layouts):
        c.post("/api/slides", json={"deck_id": d, "position": i, "layout": layout, "content": {"heading": f"[{title} slide {i + 1}]"}})
    for step in ("in review", "approved", "presented")[: ("draft", "in review", "approved", "presented").index(status)]:
        c.post(f"/api/decks/{d}/status", json={"status": step, "presented_on": "2026-10-01"})
    return d


def test_no_pattern_until_something_is_presented(c):
    deck(c, "Draft", ["title", "bullets", "closing"], status="draft")
    p = c.get("/api/decks/patterns", params={"audience": AUDIENCE}).json()
    assert p["decks_used"] == [] and p["outline"] == []
    assert c.post("/api/decks/from-pattern", json={"audience": AUDIENCE}).status_code == 400


def test_pattern_weighs_outcomes_trims_to_length_and_starts_a_deck(c):
    long_one = deck(c, "Long", ["title", "section", "bullets", "bullets", "big-number", "bullets", "comparison", "bullets", "bullets", "closing"])
    short_one = deck(c, "Short", ["title", "bullets", "big-number", "bullets", "closing"])
    c.post("/api/deck-outcomes", json={"deck_id": long_one, "landed": "mixed", "length": "too long", "detail": "needed less"})
    c.post("/api/deck-outcomes", json={"deck_id": short_one, "landed": "well", "length": "about right", "note": "[They liked the single number]"})
    p = c.get("/api/decks/patterns", params={"audience": " " + AUDIENCE.upper() + " "}).json()
    assert [d["title"] for d in p["decks_used"]] == ["Short", "Long"] and p["best_deck"]["title"] == "Short"
    assert p["target_slides"] <= 8 and p["outline"][0]["layout"] == "title" and p["outline"][-1]["layout"] == "closing"
    assert any("less detail" in a for a in p["advice"]) and any("[They liked the single number]" in a for a in p["advice"])
    assert {m["layout"] for m in p["mix"]} >= {"bullets", "title", "closing"}
    known = c.get("/api/decks/audiences").json()
    assert known[0]["audience"] == AUDIENCE and known[0]["presented"] == 2 and known[0]["outcomes"] == 2
    made = c.post("/api/decks/from-pattern", json={"audience": AUDIENCE, "title": "[Next update]"}).json()
    assert made["slides"] == len(p["outline"]) and made["facts"] is False
    full = c.get(f"/api/decks/{made['deck_id']}/full").json()
    assert full["deck"]["audience"] == AUDIENCE and full["slides"][0]["content"]["heading"] == "[Next update]"
    assert full["slides"][1]["content"]["heading"].startswith("[Last time: ") and "Started from what worked" in full["slides"][0]["notes"]
