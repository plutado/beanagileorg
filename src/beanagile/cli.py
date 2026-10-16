"""Run a supporting app: `beanagile toolkit` or `beanagile comms`. Binds to localhost only."""

import argparse

import uvicorn

from beanagile.core.config import Settings

APPS = {
    "toolkit": ("Toolkit", 8801),
    "comms": ("Comms studio", 8802),
}
LOOPBACK = {"127.0.0.1", "localhost", "::1"}


def build_app(name: str, port: int | None = None):
    title, default_port = APPS[name]
    settings = Settings(app=name, title=title, port=port or default_port)
    if name == "toolkit":
        from beanagile.toolkit.app import build
    else:
        from beanagile.comms.app import build
    return build(settings), settings


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="beanagile", description=__doc__)
    parser.add_argument("app", choices=sorted(APPS))
    parser.add_argument("--port", type=int, help="defaults: toolkit 8801, comms 8802")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--reload", action="store_true", help="restart on code changes (development)")
    args = parser.parse_args(argv)
    if args.host not in LOOPBACK:
        parser.error("These apps only listen on localhost. Timed sharing is a separate feature.")
    port = args.port or APPS[args.app][1]
    if args.reload:
        uvicorn.run(f"beanagile.cli:{args.app}_factory", factory=True, host=args.host, port=port, reload=True)
    else:
        app, _ = build_app(args.app, port)
        uvicorn.run(app, host=args.host, port=port)


def toolkit_factory():
    return build_app("toolkit")[0]


def comms_factory():
    return build_app("comms")[0]


if __name__ == "__main__":
    main()
