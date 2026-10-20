"""The sprint burndown, rebuilt from the change log, and the Product Goal."""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def env(tmp_path):
    client = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    client.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return client, tmp_path / "toolkit.db"


def backdate(db, item_id, field, value, day):
    conn = sqlite3.connect(db)
    conn.execute("UPDATE change_log SET at = ? WHERE entity = 'backlog_item' AND record_id = ? AND field = ? AND new_value = ?",
                 (f"{day} 12:00:00", str(item_id), field, value))
    conn.commit()
    conn.close()


def test_burndown_follows_done_added_and_removed_stories(env):
    c, db = env
    sprint = c.post("/api/sprints", json={"number": 1, "start_date": "2026-10-12", "end_date": "2026-10-16", "goal": "[Goal]"}).json()["id"]
    a, b, extra = (c.post("/api/backlog-items", json={"title": t, "points": p, "status": "ready"}).json()["id"]
                   for t, p in (("[Story A]", 5), ("[Story B]", 3), ("[Story C]", 2)))
    for i in (a, b):
        c.post(f"/api/sprint-planning/{sprint}/pull", json={"item_id": i})
        backdate(db, i, "sprint_id", str(sprint), "2026-10-11")
        backdate(db, i, "status", "ready", "2026-10-10")
    backdate(db, extra, "status", "ready", "2026-10-10")
    c.post(f"/api/sprint-planning/{sprint}/pull", json={"item_id": extra})
    backdate(db, extra, "sprint_id", str(sprint), "2026-10-14")
    c.patch(f"/api/backlog-items/{a}", json={"status": "done"})
    backdate(db, a, "status", "done", "2026-10-13")
    c.patch(f"/api/backlog-items/{b}", json={"status": "removed"})
    backdate(db, b, "status", "removed", "2026-10-15")

    d = c.get(f"/api/sprint-planning/{sprint}/burndown").json()
    assert [p["date"] for p in d["days"]] == ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]
    assert [p["remaining"] for p in d["days"]] == [8, 3, 5, 2, 2]
    assert [p["scope"] for p in d["days"]] == [8, 8, 10, 7, 7]
    assert d["start_scope"] == 8 and d["days"][0]["ideal"] == 8 and d["days"][-1]["ideal"] == 0
    assert d["scope_added"] == 2 and d["scope_removed"] == 3


def test_burndown_needs_dates(env):
    c, _ = env
    sprint = c.post("/api/sprints", json={"number": 1}).json()["id"]
    assert c.get(f"/api/sprint-planning/{sprint}/burndown").json()["days"] == []


def test_product_goal_shows_with_backlog_plan_and_summary(env):
    c, _ = env
    assert c.get("/api/planning/product-goal").json()["text"] == ""
    c.put("/api/planning/product-goal", json={"text": "  [Placeholder product goal]  "})
    assert c.get("/api/backlog").json()["product_goal"]["text"] == "[Placeholder product goal]"
    sprint = c.post("/api/sprints", json={"number": 1, "goal": "[Goal]"}).json()["id"]
    assert c.get(f"/api/sprint-planning/{sprint}").json()["product_goal"]["text"] == "[Placeholder product goal]"
    assert "**Product goal:** [Placeholder product goal]" in c.get(f"/api/sprint-planning/{sprint}/summary").json()["markdown"]
