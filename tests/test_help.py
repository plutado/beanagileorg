from fastapi.testclient import TestClient

from beanagileorg.comms.app import NAV as COMMS_NAV
from beanagileorg.comms.app import build as build_comms
from beanagileorg.core import coaching
from beanagileorg.core import help as help_text
from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import NAV as TOOLKIT_NAV
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


def paths(nav):
    return {n["path"] for n in nav if "path" in n} - {"/help"}


def test_every_section_has_purpose_and_steps():
    for app, nav in (("toolkit", TOOLKIT_NAV), ("comms", COMMS_NAV)):
        assert set(help_text.HELP[app]) == paths(nav), app
        for route, h in help_text.HELP[app].items():
            assert h["purpose"] and h["steps"], route
            assert all(len(s) < 220 for s in h["steps"]), route


def test_see_also_links_go_somewhere_real():
    slugs = {g["slug"] for g in coaching.GUIDES}
    for app, nav in (("toolkit", TOOLKIT_NAV), ("comms", COMMS_NAV)):
        for route, h in help_text.HELP[app].items():
            for r in h["related"]:
                ok = r in paths(nav) or r == "/coaching/reflect" or (r.startswith("/coaching/") and r.split("/")[2] in slugs)
                assert ok, f"{app} {route} -> {r}"


def test_each_app_serves_its_own_help(tmp_path):
    t = TestClient(build(Settings(app="toolkit", title="T", port=0, data_dir=tmp_path / "t")))
    t.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    c = TestClient(build_comms(Settings(app="comms", title="C", port=0, data_dir=tmp_path / "c")))
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    assert "/retros" in t.get("/api/help").json() and "/retros" not in c.get("/api/help").json()
    assert "/decks" in c.get("/api/help").json()
    assert any(n.get("path") == "/help" for n in t.get("/api/session").json()["nav"])
