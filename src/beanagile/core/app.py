"""App factory shared by every supporting app: sign-in, sessions, presentation mode, tokens and the UI shell."""

import html
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import auth, tokens
from .changelog import recent_changes
from .config import Settings
from .db import CORE_MIGRATIONS, Database, migrate
from .export import recent_exports
from .odysseus import OdysseusClient
from .privacy import SCOPE_FLOORS, Level, Viewer, floor_for_scopes, register_scope

CORE_STATIC = Path(__file__).parent / "static"
SESSION_COOKIE = "ba_session"
PUBLIC_PATHS = {"/login", "/setup", "/api/health"}
PUBLIC_PREFIXES = ("/static/", "/core-static/")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ---- dependencies shared with app routers ----------------------------------------------------


def get_conn(request: Request):
    conn = request.app.state.db.connect()
    try:
        yield conn
    finally:
        conn.close()


def get_viewer(request: Request) -> Viewer:
    return request.state.viewer


def require_full(viewer: Viewer = Depends(get_viewer)) -> Viewer:
    """Signed in directly and not presenting: needed for anything that manages access or shows private history."""
    if not viewer.is_session or viewer.presentation:
        raise HTTPException(403, "Not available to tokens or in presentation mode.")
    return viewer


def require_scope(scope: str):
    def dependency(viewer: Viewer = Depends(get_viewer)) -> Viewer:
        if not viewer.has_scope(scope):
            raise HTTPException(403, f"This needs the {scope} scope.")
        return viewer

    return dependency


# ---- request models -------------------------------------------------------------------------


class PresentationIn(BaseModel):
    on: bool


class TokenIn(BaseModel):
    name: str
    scopes: list[str]


class CodeIn(BaseModel):
    code: str


class PasswordIn(BaseModel):
    password: str


class PasswordChangeIn(BaseModel):
    current: str
    new: str


# ---- pages ----------------------------------------------------------------------------------


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<script>try {{ const t = localStorage.getItem("ba-theme"); if (t === "light" || t === "dark") document.documentElement.dataset.theme = t; }} catch (e) {{}}</script>
<link rel="stylesheet" href="/core-static/app.css"></head>
<body class="auth-page"><main class="auth-card"><div class="auth-brand"><span class="brand-mark">B</span>beanagile</div>{body}</main></body></html>"""
    )


def _error(message: str | None) -> str:
    return f'<p class="error" role="alert">{html.escape(message)}</p>' if message else ""


def _setup_page(title: str, error: str | None = None) -> HTMLResponse:
    return _page(
        f"Set up {title}",
        f"""<h1>Set up {html.escape(title)}</h1>
<p class="quiet">Choose a password for this app. It stays on this computer.</p>{_error(error)}
<form method="post" action="/setup">
<label>Password<input type="password" name="password" minlength="{auth.MIN_PASSWORD_LENGTH}" required autofocus></label>
<label>Confirm password<input type="password" name="confirm" required></label>
<button class="primary" type="submit">Create</button></form>""",
    )


def _login_page(title: str, totp: bool, error: str | None = None) -> HTMLResponse:
    code = (
        '<label>Authenticator code<input name="code" inputmode="numeric" autocomplete="one-time-code" required></label>'
        if totp
        else ""
    )
    return _page(
        f"Sign in to {title}",
        f"""<h1>{html.escape(title)}</h1>{_error(error)}
<form method="post" action="/login">
<label>Password<input type="password" name="password" required autofocus></label>{code}
<button class="primary" type="submit">Sign in</button></form>""",
    )


# ---- factory --------------------------------------------------------------------------------


def create_app(
    settings: Settings,
    *,
    nav: list[dict],
    migrations: list[tuple[int, str]] = (),
    routers: list = (),
    static_dir: Path | None = None,
    scopes: dict[str, Level] | None = None,
) -> FastAPI:
    for scope, floor in (scopes or {}).items():
        register_scope(scope, floor)

    app = FastAPI(title=settings.title, docs_url=None, redoc_url=None, openapi_url="/api/openapi.json")
    db = Database(settings.db_path)
    with db.session() as conn:
        migrate(conn, "core", CORE_MIGRATIONS)
        migrate(conn, settings.app, list(migrations))
    app.state.settings = settings
    # One cookie per app: browsers share cookies across ports, so a shared name would sign you out of the other app.
    cookie_name = f"{SESSION_COOKIE}_{settings.app}"
    app.state.db = db
    app.state.nav = nav
    app.state.throttle = auth.LoginThrottle()
    app.state.odysseus = OdysseusClient(settings.odysseus_url, settings.odysseus_token)

    def resolve_viewer(conn, request: Request) -> Viewer | None:
        header = request.headers.get("authorization", "")
        if header.lower().startswith("bearer "):
            found = tokens.lookup_token(conn, header[7:].strip())
            if not found:
                return None
            return Viewer(
                floor=floor_for_scopes(found["scopes"]),
                source=f"token:{found['name']}",
                scopes=frozenset(found["scopes"]),
            )
        cookie = request.cookies.get(cookie_name)
        if cookie:
            row = conn.execute(
                "SELECT token_hash, presentation FROM sessions WHERE token_hash = ? AND expires_at > ?",
                (auth.hash_token(cookie), _now()),
            ).fetchone()
            if row:
                presenting = bool(row["presentation"])
                return Viewer(
                    floor=Level.PRESENTABLE if presenting else Level.PRIVATE,
                    source="me",
                    scopes=frozenset({"full"}),
                    session_hash=row["token_hash"],
                    presentation=presenting,
                )
        return None

    @app.middleware("http")
    async def authenticate(request: Request, call_next):
        path = request.url.path
        with db.session() as conn:
            viewer = resolve_viewer(conn, request)
            has_user = conn.execute("SELECT 1 FROM users").fetchone() is not None
        request.state.viewer = viewer
        request.state.has_user = has_user
        if viewer is None and path not in PUBLIC_PATHS and not path.startswith(PUBLIC_PREFIXES):
            if path.startswith("/api/"):
                return JSONResponse({"detail": "Not signed in."}, status_code=401)
            return RedirectResponse("/login" if has_user else "/setup", status_code=303)
        return await call_next(request)

    def start_session(conn) -> str:
        token = auth.new_token("bas")
        expires = (datetime.now(timezone.utc) + timedelta(days=settings.session_days)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO sessions (token_hash, expires_at) VALUES (?, ?)", (auth.hash_token(token), expires))
        return token

    def signed_in(token: str) -> RedirectResponse:
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(
            cookie_name, token, httponly=True, samesite="strict", max_age=settings.session_days * 86400, path="/"
        )
        return response

    def session_payload(conn, viewer: Viewer) -> dict:
        user = conn.execute("SELECT totp_secret FROM users").fetchone()
        return {
            "app": settings.app,
            "title": settings.title,
            "nav": nav,
            "source": viewer.source,
            "presentation": viewer.presentation,
            "floor": viewer.floor.name.lower(),
            "totp_enabled": bool(user and user["totp_secret"]),
            "odysseus": app.state.odysseus.status(),
        }

    # ---- setup and sign-in ----

    @app.get("/setup")
    def setup_form(request: Request):
        if request.state.has_user:
            return RedirectResponse("/login", status_code=303)
        return _setup_page(settings.title)

    @app.post("/setup")
    def setup(request: Request, password: str = Form(...), confirm: str = Form(...), conn=Depends(get_conn)):
        if request.state.has_user:
            return RedirectResponse("/login", status_code=303)
        if len(password) < auth.MIN_PASSWORD_LENGTH:
            return _setup_page(settings.title, f"Use at least {auth.MIN_PASSWORD_LENGTH} characters.")
        if password != confirm:
            return _setup_page(settings.title, "The passwords don't match.")
        conn.execute("INSERT INTO users (id, password_hash) VALUES (1, ?)", (auth.hash_password(password),))
        return signed_in(start_session(conn))

    @app.get("/login")
    def login_form(request: Request, conn=Depends(get_conn)):
        if not request.state.has_user:
            return RedirectResponse("/setup", status_code=303)
        user = conn.execute("SELECT totp_secret FROM users").fetchone()
        return _login_page(settings.title, bool(user["totp_secret"]))

    @app.post("/login")
    def login(request: Request, password: str = Form(...), code: str = Form(""), conn=Depends(get_conn)):
        user = conn.execute("SELECT password_hash, totp_secret FROM users").fetchone()
        if user is None:
            return RedirectResponse("/setup", status_code=303)
        totp = bool(user["totp_secret"])
        client = request.client.host if request.client else "unknown"
        throttle = app.state.throttle
        if not throttle.allowed(client):
            page = _login_page(settings.title, totp, "Too many attempts. Wait a few minutes and try again.")
            page.status_code = 429
            return page
        ok = auth.verify_password(password, user["password_hash"]) and (
            not totp or auth.verify_totp(user["totp_secret"], code)
        )
        if not ok:
            throttle.fail(client)
            page = _login_page(settings.title, totp, "That didn't match.")
            page.status_code = 401
            return page
        throttle.reset(client)
        return signed_in(start_session(conn))

    @app.post("/logout")
    def logout(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
        if viewer.session_hash:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (viewer.session_hash,))
        response = RedirectResponse("/login", status_code=303)
        response.delete_cookie(cookie_name, path="/")
        return response

    # ---- core API ----

    @app.get("/api/health")
    def health():
        return {"app": settings.app, "ok": True, "odysseus": app.state.odysseus.status()}

    @app.get("/api/session")
    def session(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
        return session_payload(conn, viewer)

    @app.post("/api/session/presentation")
    def set_presentation(body: PresentationIn, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
        if not viewer.is_session:
            raise HTTPException(403, "Presentation mode belongs to a signed-in session.")
        conn.execute("UPDATE sessions SET presentation = ? WHERE token_hash = ?", (int(body.on), viewer.session_hash))
        updated = Viewer(
            floor=Level.PRESENTABLE if body.on else Level.PRIVATE,
            source=viewer.source,
            scopes=viewer.scopes,
            session_hash=viewer.session_hash,
            presentation=body.on,
        )
        return session_payload(conn, updated)

    @app.get("/api/scopes")
    def list_scopes(viewer: Viewer = Depends(require_full)):
        return [{"scope": s, "reads": floor.name.lower()} for s, floor in sorted(SCOPE_FLOORS.items())]

    @app.get("/api/tokens")
    def get_tokens(viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        return tokens.list_tokens(conn)

    @app.post("/api/tokens", status_code=201)
    def post_token(body: TokenIn, viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        try:
            token = tokens.create_token(conn, body.name, body.scopes)
        except tokens.TokenError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"token": token, "note": "Copy this now; it won't be shown again."}

    @app.delete("/api/tokens/{token_id}", status_code=204)
    def delete_token(token_id: int, viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        if not tokens.revoke_token(conn, token_id):
            raise HTTPException(404, "No active token with that id.")

    @app.post("/api/auth/totp/start")
    def totp_start(viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        secret = auth.new_totp_secret()
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('pending_totp', ?)", (secret,))
        return {"secret": secret, "uri": auth.totp_uri(secret, settings.app, f"beanagile {settings.title}")}

    @app.post("/api/auth/totp/confirm")
    def totp_confirm(body: CodeIn, viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        row = conn.execute("SELECT value FROM settings WHERE key = 'pending_totp'").fetchone()
        if row is None or not auth.verify_totp(row["value"], body.code):
            raise HTTPException(400, "That code didn't match. Try the current one.")
        conn.execute("UPDATE users SET totp_secret = ?", (row["value"],))
        conn.execute("DELETE FROM settings WHERE key = 'pending_totp'")
        return {"totp_enabled": True}

    @app.post("/api/auth/totp/disable")
    def totp_disable(body: PasswordIn, viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        user = conn.execute("SELECT password_hash FROM users").fetchone()
        if not auth.verify_password(body.password, user["password_hash"]):
            raise HTTPException(400, "That password didn't match.")
        conn.execute("UPDATE users SET totp_secret = NULL")
        return {"totp_enabled": False}

    @app.post("/api/auth/password")
    def change_password(body: PasswordChangeIn, viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        user = conn.execute("SELECT password_hash FROM users").fetchone()
        if not auth.verify_password(body.current, user["password_hash"]):
            raise HTTPException(400, "The current password didn't match.")
        if len(body.new) < auth.MIN_PASSWORD_LENGTH:
            raise HTTPException(400, f"Use at least {auth.MIN_PASSWORD_LENGTH} characters.")
        conn.execute("UPDATE users SET password_hash = ?", (auth.hash_password(body.new),))
        conn.execute("DELETE FROM sessions WHERE token_hash != ?", (viewer.session_hash,))
        return {"ok": True}

    @app.get("/api/changes")
    def changes(limit: int = 100, viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        return recent_changes(conn, min(max(limit, 1), 500))

    @app.get("/api/exports")
    def exports(viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        return recent_exports(conn)

    for router in routers:
        app.include_router(router)

    shell = (CORE_STATIC / "shell.html").read_text()

    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTMLResponse(shell.replace("{{TITLE}}", html.escape(settings.title)))

    app.mount("/core-static", StaticFiles(directory=CORE_STATIC), name="core-static")
    if static_dir is not None:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    return app
