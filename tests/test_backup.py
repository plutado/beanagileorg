import io
import json
import sqlite3
import tarfile
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from beanagileorg import cli
from beanagileorg.core import backup
from beanagileorg.core.config import Settings
from beanagileorg.comms.app import build as build_comms
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.setenv("BEANAGILEORG_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("BEANAGILEORG_BACKUP_DIR", str(tmp_path / "backups"))
    c = TestClient(build(Settings(app="toolkit", title="T", port=0, data_dir=tmp_path / "data" / "toolkit")), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    c.post("/api/people", json={"name": "[Person]"})
    media = tmp_path / "data" / "toolkit" / "media"
    media.mkdir()
    (media / "[placeholder].bin").write_bytes(b"[placeholder bytes]")
    return tmp_path, c


def test_backup_is_checked_and_restores(data):
    tmp, c = data
    d = tmp / "data" / "toolkit"
    r = backup.create_backup("toolkit", d, tmp / "backups")
    assert r["ok"] and r["files"] == 1 and r["rows"] > 0
    c.post("/api/people", json={"name": "[Added after backup]"})
    (d / "media" / "[placeholder].bin").unlink()
    out = backup.restore_backup(r["path"], d, "toolkit")
    conn = sqlite3.connect(d / "toolkit.db")
    assert [n for (n,) in conn.execute("SELECT name FROM people")] == ["[Person]"]
    assert (d / "media" / "[placeholder].bin").read_bytes() == b"[placeholder bytes]"
    assert (tmp / "data" / "toolkit" / out["set_aside"].split("/")[-1] / "toolkit.db").exists()
    assert not (d / "manifest.json").exists()


def test_damaged_backup_fails_the_check(data):
    tmp, _ = data
    r = backup.create_backup("toolkit", tmp / "data" / "toolkit", tmp / "backups")
    path = r["path"]
    with open(path, "r+b") as f:
        f.seek(40)
        f.write(b"\x00" * 64)
    assert backup.verify_backup(path)["ok"] is False
    with pytest.raises(ValueError):
        backup.restore_backup(path, tmp / "data" / "toolkit", "toolkit")


def test_row_mismatch_is_caught(data, tmp_path):
    tmp, _ = data
    r = backup.create_backup("toolkit", tmp / "data" / "toolkit", tmp / "backups")
    work = tmp_path / "unpacked"
    with tarfile.open(r["path"]) as tar:
        tar.extractall(work, filter="data")
    conn = sqlite3.connect(work / "toolkit.db")
    conn.execute("DELETE FROM people")
    conn.commit()
    conn.close()
    bad = tmp_path / "tampered.tar.gz"
    with tarfile.open(bad, "w:gz") as tar:
        for name in ("toolkit.db", "manifest.json", "media"):
            tar.add(work / name, arcname=name)
    check = backup.verify_backup(bad)
    assert not check["ok"] and any("people" in p for p in check["problems"])


def test_wrong_app_and_unsafe_archives_are_refused(data, tmp_path):
    tmp, _ = data
    r = backup.create_backup("toolkit", tmp / "data" / "toolkit", tmp / "backups")
    with pytest.raises(ValueError, match="toolkit backup, not comms"):
        backup.restore_backup(r["path"], tmp / "data" / "comms", "comms")
    evil = tmp_path / "evil.tar.gz"
    with tarfile.open(evil, "w:gz") as tar:
        info = tarfile.TarInfo("../outside.txt")
        info.size = 3
        tar.addfile(info, io.BytesIO(b"bad"))
    assert backup.verify_backup(evil)["ok"] is False
    assert not (tmp_path.parent / "outside.txt").exists()


def test_keeps_the_newest(data, monkeypatch):
    tmp, _ = data
    out = tmp / "backups" / "toolkit"
    out.mkdir(parents=True)
    for i in range(5):
        (out / f"toolkit-2026010{i}-000000.tar.gz").write_bytes(b"x")
    assert backup.prune(out, "toolkit", 2) == ["toolkit-20260102-000000.tar.gz", "toolkit-20260101-000000.tar.gz", "toolkit-20260100-000000.tar.gz"]


def test_api_backup_now(data):
    tmp, c = data
    r = c.post("/api/backups").json()
    assert r["ok"]
    listed = c.get("/api/backups").json()
    assert listed["count"] == 1 and listed["backups"][0]["ok"] is True
    anon = TestClient(c.app)
    assert anon.post("/api/backups").status_code == 401


def test_cli_backup_list_verify_and_domain(data, capsys):
    tmp, _ = data
    assert cli.main(["backup", "all"]) == 0
    out = capsys.readouterr().out
    assert "toolkit:" in out and "restores cleanly" in out and "comms: no data yet" in out
    assert cli.main(["backups", "toolkit"]) == 0 and " ok" in capsys.readouterr().out
    archive = next((tmp / "backups" / "toolkit").glob("*.tar.gz"))
    assert cli.main(["verify", str(archive)]) == 0
    assert cli.main(["domain"]) == 0
    text = capsys.readouterr().out
    assert "127.0.0.1  toolkit.beanagile.org" in text and "reverse_proxy 127.0.0.1:8802" in text
    plist = backup.launchd_plist("/usr/local/bin/beanagileorg", 3, 15)
    assert "<integer>3</integer>" in plist and "<string>all</string>" in plist


# ---- the Today warning when the last good backup is more than two days old ----


def test_today_warns_with_no_backups(data):
    _, c = data
    assert c.get("/api/today").json()["backup"] == {"last_good": None, "days": None}


def test_today_is_quiet_after_a_fresh_good_backup(data):
    _, c = data
    assert c.post("/api/backups").json()["ok"]
    assert c.get("/api/today").json()["backup"] is None


def test_old_good_backup_warns(data):
    tmp, _ = data
    made = backup.create_backup("toolkit", tmp / "data" / "toolkit", tmp / "backups")
    taken = datetime.fromisoformat(made["at"])
    assert backup.backup_warning("toolkit", tmp / "backups", now=taken + timedelta(hours=47)) is None
    late = backup.backup_warning("toolkit", tmp / "backups", now=taken + timedelta(days=3, hours=1))
    assert late == {"last_good": made["at"], "days": 3}


def test_failed_backup_does_not_count_as_good(data, monkeypatch):
    tmp, c = data
    monkeypatch.setattr(backup, "verify_backup", lambda archive: {"ok": False, "problems": ["[Placeholder problem]"], "manifest": None})
    assert c.post("/api/backups").json()["ok"] is False
    assert c.get("/api/backups").json()["count"] == 1
    assert c.get("/api/today").json()["backup"] == {"last_good": None, "days": None}


def test_a_recent_failure_does_not_hide_an_old_good_backup(data):
    tmp, _ = data
    good = backup.create_backup("toolkit", tmp / "data" / "toolkit", tmp / "backups")
    out = tmp / "backups" / "toolkit"
    old = (datetime.fromisoformat(good["at"]) - timedelta(days=5)).isoformat(timespec="seconds")
    (out / "backup-log.jsonl").write_text((out / "backup-log.jsonl").read_text().replace(good["at"], old))
    (out / "toolkit-29990101-000000.tar.gz").write_bytes(b"[placeholder broken archive]")
    with open(out / "backup-log.jsonl", "a") as f:
        f.write(json.dumps({"at": good["at"], "file": "toolkit-29990101-000000.tar.gz", "ok": False, "problems": ["[Placeholder problem]"]}) + "\n")
    assert backup.backup_warning("toolkit", tmp / "backups") == {"last_good": old, "days": 5}


def test_backup_warning_hidden_while_presenting(data):
    _, c = data
    c.post("/api/session/presentation", json={"on": True})
    assert c.get("/api/today").json() == {"hidden": True}


def test_comms_this_week_carries_the_warning(tmp_path, monkeypatch):
    monkeypatch.setenv("BEANAGILEORG_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("BEANAGILEORG_BACKUP_DIR", str(tmp_path / "backups"))
    c = TestClient(build_comms(Settings(app="comms", title="C", port=0, data_dir=tmp_path / "data" / "comms")), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    assert c.get("/api/this-week").json()["backup"] == {"last_good": None, "days": None}
    assert c.post("/api/backups").json()["ok"]
    assert c.get("/api/this-week").json()["backup"] is None
    (tmp_path / "backups" / "comms" / "backup-log.jsonl").unlink()
    c.post("/api/session/presentation", json={"on": True})
    assert c.get("/api/this-week").json()["backup"] is None
