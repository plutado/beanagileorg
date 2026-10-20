"""The Scrum events: the sprint review adjusting the backlog, retro improvements into the next sprint, and timeboxes."""

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def c(tmp_path):
    client = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    client.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return client


def test_review_lists_done_work_and_turns_feedback_into_backlog_items(c):
    c.put("/api/planning/product-goal", json={"text": "[Product goal]"})
    sprint = c.post("/api/sprints", json={"number": 4, "goal": "[Sprint goal]"}).json()["id"]
    done, open_ = (c.post("/api/backlog-items", json={"title": t, "points": 3, "status": "ready", "jira_key": k}).json()["id"]
                   for t, k in (("[Done story]", "ABC-1"), ("[Open story]", "ABC-2")))
    for i in (done, open_):
        c.post(f"/api/sprint-planning/{sprint}/pull", json={"item_id": i})
    c.patch(f"/api/backlog-items/{done}", json={"status": "done"})
    r = c.get(f"/api/sprint-planning/{sprint}/review").json()
    assert [i["title"] for i in r["done"]] == ["[Done story]"] and [i["title"] for i in r["not_done"]] == ["[Open story]"]
    assert "**Sprint goal:** [Sprint goal]" in r["markdown"] and "- ABC-1 [Done story]" in r["markdown"] and r["timebox"]
    assert c.post(f"/api/sprint-planning/{sprint}/review/feedback", json={"text": " "}).status_code == 400
    item = c.post(f"/api/sprint-planning/{sprint}/review/feedback", json={"text": "[Stakeholder idea]", "from": "[Name 1]"}).json()
    assert item["status"] == "needs refinement" and item["labels"] == ["sprint review", "sprint 4"] and "[Name 1]" in item["description"]
    assert [i["title"] for i in c.get("/api/backlog").json()["items"]] == ["[Stakeholder idea]"]
    assert c.get(f"/api/sprint-planning/{sprint}/review").json()["feedback"][0]["title"] == "[Stakeholder idea]"


def test_retro_commitment_becomes_a_ready_backlog_item_once(c):
    rid = c.post("/api/retros", json={"date": "2026-10-20", "format": "start / stop / continue"}).json()["id"]
    cm = c.post("/api/retro-commitments", json={"retro_id": rid, "commitment": "[Pair on reviews]"}).json()["id"]
    item = c.post(f"/api/retro-commitments/{cm}/to-backlog").json()
    assert item["status"] == "ready" and item["item_type"] == "task" and "retro improvement" in item["labels"]
    assert c.post(f"/api/retro-commitments/{cm}/to-backlog").status_code == 409


def test_planning_shows_timeboxes_for_the_sprint_length(c):
    c.put("/api/agile/sprint-length", json={"weeks": 2})
    sprint = c.post("/api/sprints", json={"number": 1}).json()["id"]
    t = c.get(f"/api/sprint-planning/{sprint}").json()["timeboxes"]
    assert t["weeks"] == 2 and t["planning"].startswith("Up to 4 hours") and t["review"].startswith("Up to 2 hours")


def test_invest_checks_join_the_definition_of_ready_once_and_enablers_are_a_type(c):
    c.put("/api/planning/definition-of-ready", json={"items": ["[Our own check]"]})
    items = c.post("/api/planning/definition-of-ready/invest").json()["items"]
    assert items[0] == "[Our own check]" and len(items) == 7 and items[1].startswith("Independent:")
    assert len(c.post("/api/planning/definition-of-ready/invest").json()["items"]) == 7
    assert c.post("/api/backlog-items", json={"title": "[Enabler]", "item_type": "enabler"}).json()["item_type"] == "enabler"
