from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.comms import messaging
from beanagileorg.comms.app import build as build_comms
from beanagileorg.core import coaching as starter
from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import NAV, build

PASSWORD = "[placeholder-password]"


def make(path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


@pytest.fixture
def client(tmp_path):
    return make(tmp_path)


def test_starter_content_is_consistent():
    slugs = {g["slug"] for g in starter.GUIDES}
    assert len(slugs) == len(starter.GUIDES)
    assert all(slug in slugs for _, _, slug, _ in starter.tip_entries())
    themes = {k for k, _, _ in starter.THEMES}
    assert all(g["theme"] in themes for g in starter.GUIDES)
    toolkit_paths = {n["path"] for n in NAV if "path" in n}
    related = {r.split("/")[1] for g in starter.GUIDES for r in g["related"]}
    assert related <= {p.split("/")[1] for p in toolkit_paths}


def test_seeded_once_and_deletions_stick(tmp_path):
    c = make(tmp_path)
    lib = c.get("/api/coaching/library").json()
    assert len(lib["guides"]) == len(starter.GUIDES) and lib["restorable"] == []
    gid = next(g["id"] for g in lib["guides"] if g["slug"] == "assertiveness")
    c.delete(f"/api/coaching-guides/{gid}")
    again = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)  # a restart
    again.post("/login", data={"password": PASSWORD})
    lib = again.get("/api/coaching/library").json()
    assert "assertiveness" not in {g["slug"] for g in lib["guides"]}
    assert lib["restorable"] == [{"slug": "assertiveness", "title": "Being assertive without being abrasive"}]
    assert again.post("/api/coaching/restore/assertiveness").json()["origin"] == "built-in"
    assert again.post("/api/coaching/restore/assertiveness").status_code == 409
    assert again.post("/api/coaching/restore/nope").status_code == 404


def test_write_and_edit_guides(client):
    g = client.post("/api/coaching-guides", json={"title": "[My guide: on courage]", "inspired_by": "[Book, chapter]"}).json()
    assert g["slug"] == "my-guide-on-courage" and g["origin"] == "mine"
    assert client.post("/api/coaching-guides", json={"title": "[My guide: on courage]"}).json()["slug"] == "my-guide-on-courage-2"
    assert client.post("/api/coaching-guides", json={"title": "[X]", "slug": "my-guide-on-courage"}).status_code == 409
    assert client.post("/api/coaching-guides", json={"title": " "}).status_code == 400
    client.patch(f"/api/coaching-guides/{g['id']}", json={"practices": ["[One]", "[Two]"], "focus": "practicing", "my_notes": "[Private]"})
    d = client.get("/api/coaching/guide/my-guide-on-courage").json()["guide"]
    assert d["practices"] == ["[One]", "[Two]"] and d["focus"] == "practicing"
    assert client.get("/api/coaching/guide/missing").status_code == 404


def test_tips_follow_edits(client):
    tips = client.get("/api/coaching/tips").json()
    assert set(tips) == set(starter.TIPS) and tips["/retros"][0]["guide"] == "retros"
    first = tips["/retros"][0]["id"]
    client.patch(f"/api/coaching-tips/{first}", json={"active": False})
    gid = next(g["id"] for g in client.get("/api/coaching/library").json()["guides"] if g["slug"] == "psychological-safety")
    client.patch(f"/api/coaching-guides/{gid}", json={"status": "draft"})
    retro = client.get("/api/coaching/tips").json()["/retros"]
    assert len(retro) == 1 and retro[0]["guide"] is None


def test_reflection_journal(client):
    client.put("/api/toolkit/settings", json={"start_date": (date.today() - timedelta(days=9)).isoformat()})
    d = client.get("/api/coaching/reflect").json()
    assert d["day"] == 10 and d["phase"] == "Weeks 2 to 4" and d["prompts"] and d["anytime"]
    client.post("/api/reflections", json={"date": date.today().isoformat(), "entry": "[Private reflection]", "energy": 3, "confidence": 4})
    d = client.get("/api/coaching/reflect").json()
    assert d["entries"][0]["entry"] == "[Private reflection]" and d["trend"][-1]["energy"] == 3
    client.post("/api/session/presentation", json={"on": True})
    assert client.get("/api/coaching/reflect").json() == {"hidden": True}
    assert client.get("/api/reflections").json() == []


def test_pack_round_trip_keeps_private_things_private(tmp_path):
    a = make(tmp_path / "a")
    g = a.post("/api/coaching-guides", json={"title": "[Shared guide]", "my_notes": "[Mine only]", "focus": "practicing"}).json()
    a.post("/api/coaching-guides", json={"title": "[Draft guide]", "status": "draft"})
    pack = a.post("/api/coaching/pack/export").json()
    text = repr(pack)
    assert "[Shared guide]" in text and "[Mine only]" not in text and "practicing" not in text and "[Draft guide]" not in text
    assert a.get("/api/exports").json()[0]["kind"] == "coaching:pack"
    b = make(tmp_path / "b")
    r = b.post("/api/coaching/pack/import", json={"pack": pack}).json()
    assert r["guides_added"] == 1 and r["guides_skipped"] == len(starter.GUIDES) and r["tips_added"] == 0
    bid = next(x["id"] for x in b.get("/api/coaching/library").json()["guides"] if x["slug"] == g["slug"])
    b.patch(f"/api/coaching-guides/{bid}", json={"my_notes": "[B's note]"})
    pack["guides"] = [dict(x, summary="[Updated]") for x in pack["guides"] if x["slug"] == g["slug"]]
    assert b.post("/api/coaching/pack/import", json={"pack": pack, "replace": True}).json()["guides_replaced"] == 1
    got = b.get(f"/api/coaching/guide/{g['slug']}").json()["guide"]
    assert got["summary"] == "[Updated]" and got["my_notes"] == "[B's note]" and got["origin"] == "imported"
    assert b.post("/api/coaching/pack/import", json={"pack": {"kind": "other"}}).status_code == 400


def test_comms_tips_from_toolkit_or_built_in(tmp_path, monkeypatch):
    comms = TestClient(build_comms(Settings(app="comms", title="Comms", port=0, data_dir=tmp_path / "comms")), follow_redirects=False)
    comms.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    r = comms.get("/api/coaching/tips").json()
    assert r["source"] == "built-in" and "/messages" in r["tips"] and "/retros" not in r["tips"]
    comms.put("/api/connections", json={"toolkit_url": "http://127.0.0.1:8801", "toolkit_token": "ba_[placeholder]"})
    monkeypatch.setattr(messaging, "fetch_toolkit", lambda url, token, path, timeout=5.0: {"/messages": [{"text": "[Edited tip]", "guide": None, "title": None}], "/retros": []})
    r = comms.get("/api/coaching/tips").json()
    assert r["source"] == "toolkit" and r["tips"] == {"/messages": [{"text": "[Edited tip]", "guide": None, "title": None}]}
    assert r["guide_base"] == "http://127.0.0.1:8801/#/coaching/"
