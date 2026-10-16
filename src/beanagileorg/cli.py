"""beanagileorg: run a supporting app (localhost only), and look after its data.

  beanagileorg toolkit | comms          run an app
  beanagileorg backup toolkit|comms|all back up, then check the backup by restoring it to a scratch folder
  beanagileorg backups toolkit|comms    list backups and their check results
  beanagileorg verify FILE              check a backup without changing anything
  beanagileorg restore FILE --app NAME  put a backup back (stop the app first); current data is set aside, not deleted
  beanagileorg schedule                 print a launchd job for nightly backups (--write saves it to ~/Library/LaunchAgents)
  beanagileorg domain [--caddyfile]     print the local beanagile.org setup: hosts lines and a Caddy config
"""

import argparse
import shutil
import sys
from pathlib import Path

from beanagileorg.core.config import Settings

APPS = {
    "toolkit": ("Toolkit", 8801),
    "comms": ("Comms studio", 8802),
}
LOOPBACK = {"127.0.0.1", "localhost", "::1"}
DOMAIN = "beanagile.org"


def build_app(name: str, port: int | None = None):
    title, default_port = APPS[name]
    settings = Settings(app=name, title=title, port=port or default_port)
    if name == "toolkit":
        from beanagileorg.toolkit.app import build
    else:
        from beanagileorg.comms.app import build
    return build(settings), settings


def data_dir(app: str) -> Path:
    from beanagileorg.core.backup import data_root

    return data_root() / app


def _run(args, parser) -> None:
    import uvicorn

    if args.host not in LOOPBACK:
        parser.error("These apps only listen on localhost. Timed sharing is a separate feature.")
    port = args.port or APPS[args.command][1]
    if args.reload:
        uvicorn.run(f"beanagileorg.cli:{args.command}_factory", factory=True, host=args.host, port=port, reload=True)
    else:
        app, _ = build_app(args.command, port)
        uvicorn.run(app, host=args.host, port=port)


def _backup(args) -> int:
    from beanagileorg.core import backup

    failed = 0
    for app in sorted(APPS) if args.app == "all" else [args.app]:
        if not (data_dir(app) / f"{app}.db").exists():
            print(f"{app}: no data yet, skipped")
            continue
        r = backup.create_backup(app, data_dir(app), args.dest, args.keep)
        status = "checked, restores cleanly" if r["ok"] else "FAILED its check: " + "; ".join(r["problems"])
        print(f"{app}: {r['path']} ({r['bytes'] // 1024} KB, {r['rows']} rows, {r['files']} files), {status}")
        if r["pruned"]:
            print(f"{app}: removed {len(r['pruned'])} older backup(s), keeping {args.keep}")
        failed += not r["ok"]
    return 1 if failed else 0


def _list(args) -> int:
    from beanagileorg.core import backup

    rows = backup.list_backups(args.app, args.dest)
    if not rows:
        print(f"No {args.app} backups in {backup.backup_root() if not args.dest else args.dest}.")
    for r in rows:
        status = "ok" if r.get("ok") else ("FAILED" if r.get("ok") is False else "not checked")
        print(f"{r['file']}  {r['bytes'] // 1024:>6} KB  {status}")
    return 0


def _verify(args) -> int:
    from beanagileorg.core import backup

    r = backup.verify_backup(Path(args.file))
    if r["ok"]:
        m = r["manifest"]
        print(f"OK: {m['app']} backup from {m['created']}, {sum(m['tables'].values())} rows in {len(m['tables'])} tables.")
        return 0
    print("FAILED:\n- " + "\n- ".join(r["problems"]))
    return 1


def _restore(args) -> int:
    from beanagileorg.core import backup

    port = APPS[args.app][1]
    if backup.port_in_use(port) and not args.force:
        print(f"Something is answering on port {port}. Stop the {args.app} app first (or pass --force if that's something else).")
        return 1
    try:
        r = backup.restore_backup(Path(args.file), data_dir(args.app), args.app)
    except ValueError as exc:
        print(exc)
        return 1
    print(f"Restored {r['restored']} ({r['rows']} rows). Your previous data is in {r['set_aside']}.")
    return 0


def _schedule(args) -> int:
    from beanagileorg.core import backup

    exe = shutil.which("beanagileorg") or str(Path(sys.executable).parent / "beanagileorg")
    plist = backup.launchd_plist(exe, args.hour, args.minute)
    if not args.write:
        print(plist)
        print(f"# Save with --write, then load it with:\n#   launchctl load ~/Library/LaunchAgents/{backup.LAUNCHD_LABEL}.plist")
        return 0
    target = Path.home() / "Library/LaunchAgents" / f"{backup.LAUNCHD_LABEL}.plist"
    target.parent.mkdir(parents=True, exist_ok=True)
    (backup.data_root() / "backups").mkdir(parents=True, exist_ok=True)
    target.write_text(plist)
    print(f"Saved {target}.\nTurn it on:  launchctl load {target}\nTurn it off: launchctl unload {target}")
    return 0


def caddyfile() -> str:
    return "\n\n".join(f"{app}.{DOMAIN} {{\n\ttls internal\n\treverse_proxy 127.0.0.1:{port}\n}}" for app, (_, port) in APPS.items()) + "\n"


def domain_setup() -> str:
    hosts = "\n".join(f"127.0.0.1  {app}.{DOMAIN}" for app in APPS)
    sites = caddyfile().rstrip()
    return f"""# Local beanagile.org: see docs/local-domain.md for the full steps.

# 1. Point the names at this machine. Either add these lines to /etc/hosts (sudo) ...
{hosts}
# ... or create DNS A records for them that point to 127.0.0.1 at your registrar.

# 2. Caddyfile (HTTPS with Caddy's local certificate authority):
{sites}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="beanagileorg", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, (title, port) in APPS.items():
        p = sub.add_parser(name, help=f"run the {title} (port {port})")
        p.add_argument("--port", type=int, help=f"default {port}")
        p.add_argument("--host", default="127.0.0.1")
        p.add_argument("--reload", action="store_true", help="restart on code changes (development)")
    p = sub.add_parser("backup", help="back up and check")
    p.add_argument("app", choices=[*sorted(APPS), "all"])
    p.add_argument("--dest", type=Path, help="backup folder (default ~/.beanagileorg/backups or BEANAGILEORG_BACKUP_DIR)")
    p.add_argument("--keep", type=int, default=30, help="how many backups to keep per app (default 30)")
    p = sub.add_parser("backups", help="list backups")
    p.add_argument("app", choices=sorted(APPS))
    p.add_argument("--dest", type=Path)
    p = sub.add_parser("verify", help="check a backup")
    p.add_argument("file")
    p = sub.add_parser("restore", help="restore a backup")
    p.add_argument("file")
    p.add_argument("--app", required=True, choices=sorted(APPS))
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("schedule", help="nightly backups with launchd")
    p.add_argument("--hour", type=int, default=2)
    p.add_argument("--minute", type=int, default=0)
    p.add_argument("--write", action="store_true")
    p = sub.add_parser("domain", help="local beanagile.org setup")
    p.add_argument("--caddyfile", action="store_true", help="print only the Caddy config, ready to save")
    args = parser.parse_args(argv)
    if args.command in APPS:
        _run(args, parser)
        return 0
    if args.command == "domain":
        print(caddyfile() if args.caddyfile else domain_setup(), end="" if args.caddyfile else "\n")
        return 0
    return {"backup": _backup, "backups": _list, "verify": _verify, "restore": _restore, "schedule": _schedule}[args.command](args)


def toolkit_factory():
    return build_app("toolkit")[0]


def comms_factory():
    return build_app("comms")[0]


if __name__ == "__main__":
    sys.exit(main())
