"""Backups: a consistent snapshot of an app's database and files, checked by restoring it right away.

Each backup is one .tar.gz holding the database, the app's media folder (if any) and a manifest with row counts.
After writing it, the archive is unpacked into a scratch folder and checked: SQLite's integrity check, the same
row count in every table, the same files. A backup that fails the check is reported as failed, not kept quietly.
"""

import json
import os
import shutil
import socket
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_KEEP = 30
FILE_DIRS = ("media",)


def data_root() -> Path:
    return Path(os.environ.get("BEANAGILEORG_DATA", Path.home() / ".beanagileorg"))


def backup_root() -> Path:
    return Path(os.environ.get("BEANAGILEORG_BACKUP_DIR") or data_root() / "backups")


def _counts(db: Path) -> dict[str, int]:
    conn = sqlite3.connect(db)
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    finally:
        conn.close()


def _files(folder: Path) -> dict[str, int]:
    return {str(p.relative_to(folder)): p.stat().st_size for p in sorted(folder.rglob("*")) if p.is_file()} if folder.is_dir() else {}


def _log(app_dir: Path, entry: dict) -> None:
    with open(app_dir / "backup-log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")


def create_backup(app: str, data_dir: Path, dest: Path | None = None, keep: int = DEFAULT_KEEP) -> dict:
    data_dir = Path(data_dir)
    db = data_dir / f"{app}.db"
    if not db.exists():
        raise FileNotFoundError(f"No {app} database at {db}.")
    out_dir = Path(dest or backup_root()) / app
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc)
    name = f"{app}-{stamp.strftime('%Y%m%d-%H%M%S')}.tar.gz"
    archive = out_dir / name
    with tempfile.TemporaryDirectory() as tmp:
        snap = Path(tmp) / f"{app}.db"
        src, dst = sqlite3.connect(db), sqlite3.connect(snap)
        try:
            src.backup(dst)  # consistent even while the app is running
        finally:
            src.close()
            dst.close()
        files = {d: _files(data_dir / d) for d in FILE_DIRS}
        manifest = {
            "app": app,
            "created": stamp.isoformat(timespec="seconds"),
            "tables": _counts(snap),
            "files": files,
            "source": str(data_dir),
        }
        (Path(tmp) / "manifest.json").write_text(json.dumps(manifest, indent=2))
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(snap, arcname=f"{app}.db")
            tar.add(Path(tmp) / "manifest.json", arcname="manifest.json")
            for d in FILE_DIRS:
                if (data_dir / d).is_dir():
                    tar.add(data_dir / d, arcname=d)
    os.chmod(archive, 0o600)
    check = verify_backup(archive)
    entry = {"at": manifest["created"], "file": name, "bytes": archive.stat().st_size, "ok": check["ok"], "problems": check["problems"],
             "rows": sum(manifest["tables"].values()), "files": sum(len(v) for v in files.values())}
    _log(out_dir, entry)
    pruned = prune(out_dir, app, keep)
    return {**entry, "path": str(archive), "pruned": pruned}


def _safe_extract(tar: tarfile.TarFile, dest: Path) -> None:
    root = dest.resolve()
    for member in tar.getmembers():
        target = (dest / member.name).resolve()
        if root not in target.parents and target != root:
            raise ValueError(f"Unsafe path in archive: {member.name}")
        if member.issym() or member.islnk():
            raise ValueError(f"Links aren't allowed in a backup: {member.name}")
    tar.extractall(dest, filter="data")


def verify_backup(archive: Path) -> dict:
    """Restore into a scratch folder and compare with the manifest."""
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        try:
            with tarfile.open(archive, "r:gz") as tar:
                _safe_extract(tar, Path(tmp))
            manifest = json.loads((Path(tmp) / "manifest.json").read_text())
        except (OSError, ValueError, tarfile.TarError, json.JSONDecodeError) as exc:
            return {"ok": False, "problems": [f"Couldn't open the backup: {exc}"], "manifest": None}
        db = Path(tmp) / f"{manifest['app']}.db"
        try:
            conn = sqlite3.connect(db)
            result = conn.execute("PRAGMA integrity_check").fetchone()[0]
            conn.close()
            if result != "ok":
                problems.append(f"Integrity check: {result}")
            restored = _counts(db)
        except sqlite3.DatabaseError as exc:
            return {"ok": False, "problems": [f"The database doesn't open: {exc}"], "manifest": manifest}
        for table, n in manifest["tables"].items():
            if restored.get(table) != n:
                problems.append(f"{table}: expected {n} rows, found {restored.get(table)}")
        for d, files in manifest["files"].items():
            if _files(Path(tmp) / d) != files:
                problems.append(f"The {d} folder doesn't match")
    return {"ok": not problems, "problems": problems, "manifest": manifest}


def prune(out_dir: Path, app: str, keep: int) -> list[str]:
    archives = sorted(out_dir.glob(f"{app}-*.tar.gz"), reverse=True)
    gone = []
    for old in archives[keep:]:
        old.unlink()
        gone.append(old.name)
    return gone


def list_backups(app: str, dest: Path | None = None) -> list[dict]:
    out_dir = Path(dest or backup_root()) / app
    log = {}
    if (out_dir / "backup-log.jsonl").exists():
        for line in (out_dir / "backup-log.jsonl").read_text().splitlines():
            try:
                e = json.loads(line)
                log[e["file"]] = e
            except (json.JSONDecodeError, KeyError):
                continue
    return [{"file": p.name, "bytes": p.stat().st_size, **{k: v for k, v in log.get(p.name, {}).items() if k != "file"}}
            for p in sorted(out_dir.glob(f"{app}-*.tar.gz"), reverse=True)]


def port_in_use(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def restore_backup(archive: Path, data_dir: Path, app: str) -> dict:
    """Check the backup, set the current data aside, then unpack. Run it with the app stopped."""
    archive, data_dir = Path(archive), Path(data_dir)
    check = verify_backup(archive)
    if not check["ok"]:
        raise ValueError("This backup failed its check, so nothing was changed: " + "; ".join(check["problems"]))
    if check["manifest"]["app"] != app:
        raise ValueError(f"This is a {check['manifest']['app']} backup, not {app}.")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    aside = data_dir / f"before-restore-{stamp}"
    aside.mkdir(parents=True)
    for name in (f"{app}.db", f"{app}.db-wal", f"{app}.db-shm", *FILE_DIRS):
        if (data_dir / name).exists():
            shutil.move(str(data_dir / name), aside / name)
    with tarfile.open(archive, "r:gz") as tar:
        _safe_extract(tar, data_dir)
    (data_dir / "manifest.json").unlink(missing_ok=True)
    return {"restored": archive.name, "set_aside": str(aside), "rows": sum(check["manifest"]["tables"].values())}


LAUNCHD_LABEL = "org.beanagileorg.backup"


def launchd_plist(executable: str, hour: int = 2, minute: int = 0) -> str:
    """A launchd job that backs up every app nightly. launchd runs a missed job when the Mac wakes."""
    env = "".join(f"<key>{k}</key><string>{os.environ[k]}</string>" for k in ("BEANAGILEORG_DATA", "BEANAGILEORG_BACKUP_DIR") if os.environ.get(k))
    log = data_root() / "backups" / "launchd.log"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{LAUNCHD_LABEL}</string>
  <key>ProgramArguments</key><array><string>{executable}</string><string>backup</string><string>all</string></array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>{hour}</integer><key>Minute</key><integer>{minute}</integer></dict>
  <key>EnvironmentVariables</key><dict>{env}</dict>
  <key>StandardOutPath</key><string>{log}</string>
  <key>StandardErrorPath</key><string>{log}</string>
</dict>
</plist>
"""
