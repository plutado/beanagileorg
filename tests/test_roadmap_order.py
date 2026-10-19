"""Roadmap: reordering by drag, and the starter metrics including all four DORA measures."""

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def test_reorder(client):
    ids = [client.post("/api/roadmap", json={"title": f"[Item {n}]", "target_day": 30}).json()["id"] for n in range(3)]
    assert client.post("/api/roadmap/reorder", json={"ids": [ids[2], ids[0], ids[1]]}).json()["order"] == [ids[2], ids[0], ids[1]]
    assert [i["id"] for i in client.get("/api/roadmap").json()] == [ids[2], ids[0], ids[1]]
    assert client.post("/api/roadmap/reorder", json={"ids": [999]}).status_code == 400


def test_starter_metrics_include_time_to_restore(client):
    client.post("/api/delivery/starter")
    names = {m["name"] for m in client.get("/api/metrics").json()}
    assert {"Cycle time", "Deployment frequency", "Change failure rate", "Time to restore"} <= names
