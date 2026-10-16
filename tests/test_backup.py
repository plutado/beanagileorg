import io
import sqlite3
import tarfile

import pytest
from fastapi.testclient import TestClient

from beanagileorg import cli
from beanagileorg.core import backup
from beanagileorg.core.config import Settings
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
