import json

import pytest
from fastapi.testclient import TestClient

from beanagileorg.comms import mediafiles
from beanagileorg.comms.app import build
from beanagileorg.core.config import Settings

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="comms", title="Comms", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    c.data_dir = tmp_path
    return c


def new_deck(client, title="[Placeholder deck]"):
    return client.post("/api/decks", json={"title": title}).json()["id"]


def upload(client, filename, data, **form):
    return client.post("/api/media/upload", files={"file": (filename, data)}, data=form)


def test_placeholder_deck_has_every_layout(client):
    res = client.post("/api/comms/seed-placeholders").json()
    full = client.get(f"/api/decks/{res['deck_id']}/full").json()
    layouts = [s["layout"] for s in full["slides"]]
    assert len(set(layouts)) == 11
    assert all(s["notes"].startswith("[Placeholder") for s in full["slides"])
    kinds = {m["kind"] for m in full["media"]}
    assert kinds == {"audio", "lottie"}
    lottie = next(m for m in full["media"] if m["kind"] == "lottie")
    anim = client.get(f"/api/media/{lottie['id']}/file").json()
    assert anim["layers"] and anim["nm"] == "[Placeholder animation]"


def test_add_duplicate_and_reorder_slides(client):
    deck = new_deck(client)
    a = client.post(f"/api/decks/{deck}/slides", json={"layout": "title", "content": {"heading": "[A]"}}).json()
    c = client.post(f"/api/decks/{deck}/slides", json={"layout": "closing", "content": {"heading": "[C]"}}).json()
    b = client.post(f"/api/decks/{deck}/slides", json={"layout": "bullets", "content": {"heading": "[B]"}, "after_id": a["id"]}).json()
    order = lambda: [s["content"]["heading"] for s in client.get(f"/api/decks/{deck}/full").json()["slides"]]
    assert order() == ["[A]", "[B]", "[C]"]
    client.post(f"/api/slides/{b['id']}/duplicate")
    assert order() == ["[A]", "[B]", "[B]", "[C]"]
    ids = [s["id"] for s in client.get(f"/api/decks/{deck}/full").json()["slides"]]
    client.post(f"/api/decks/{deck}/reorder", json={"slide_ids": list(reversed(ids))})
    assert order() == ["[C]", "[B]", "[B]", "[A]"]
    assert client.post(f"/api/decks/{deck}/reorder", json={"slide_ids": ids[:2]}).status_code == 400
    assert c["id"] in ids


def test_slide_validation(client):
    deck = new_deck(client)
    assert client.post(f"/api/decks/{deck}/slides", json={"layout": "spinner"}).status_code == 400
    assert client.post(f"/api/decks/{deck}/slides", json={"layout": "title", "content": "text"}).status_code == 400
    assert client.post("/api/decks/999/slides", json={"layout": "title"}).status_code == 404


def test_upload_kinds_and_checks(client):
    assert upload(client, "anim.json", mediafiles.placeholder_lottie()).json()["kind"] == "lottie"
    assert upload(client, "tone.wav", mediafiles.placeholder_tone(0.2)).json()["mime"] == "audio/wav"
    assert upload(client, "c.vtt", b"WEBVTT\n\n00:00.000 --> 00:01.000\n[Placeholder]\n").json()["kind"] == "captions"
    assert upload(client, "x.exe", b"MZ").status_code == 400
    assert upload(client, "bad.json", b"{not json").status_code == 400
    assert upload(client, "data.json", json.dumps({"rows": []}).encode()).status_code == 400
    assert upload(client, "c.vtt", b"not captions").status_code == 400
    assert upload(client, "empty.mp4", b"").status_code == 400
    assert client.post("/api/media", json={"kind": "video", "name": "x", "file_name": "x", "mime": "x", "size_bytes": 1}).status_code == 400


def test_media_serving_supports_seeking_and_delete_removes_file(client):
    rec = upload(client, "tone.wav", mediafiles.placeholder_tone(0.5), name="[Placeholder tone]", source="placeholder").json()
    res = client.get(f"/api/media/{rec['id']}/file")
    assert res.status_code == 200 and res.headers["x-content-type-options"] == "nosniff"
    ranged = client.get(f"/api/media/{rec['id']}/file", headers={"Range": "bytes=0-99"})
    assert ranged.status_code == 206 and len(ranged.content) == 100
    path = client.data_dir / "media" / rec["file_name"]
    assert path.is_file()
    assert client.delete(f"/api/media/{rec['id']}").status_code == 204
    assert not path.exists()
    assert client.get(f"/api/media/{rec['id']}/file").status_code == 404


def test_license_reference_is_private(client):
    upload(client, "a.json", mediafiles.placeholder_lottie(), license_ref="[Placeholder license]")
    assert client.get("/api/media").json()[0]["license_ref"] == "[Placeholder license]"
    client.post("/api/session/presentation", json={"on": True})
    assert "license_ref" not in client.get("/api/media").json()[0]


def test_present_page_and_vendored_libraries(client):
    deck = new_deck(client)
    page = client.get(f"/present/{deck}")
    assert page.status_code == 200 and f"window.DECK_ID = {deck}" in page.text
    for path in (
        "/static/vendor/reveal/reveal.js",
        "/static/vendor/reveal/plugin/notes.js",
        "/static/vendor/lottie/lottie_light.min.js",
        "/static/deck-render.js",
    ):
        assert client.get(path).status_code == 200, path
    anon = TestClient(client.app, follow_redirects=False)
    assert anon.get(f"/present/{deck}").status_code == 303
