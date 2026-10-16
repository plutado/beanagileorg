# beanagile

Local-first supporting apps for engineering leaders. Each app runs on your own machine, listens only on localhost, and keeps its data in a SQLite file outside this repository.

- **Toolkit** (`beanagile toolkit`, port 8801): team, listening tour, sprints, roadmap, status and my development.
- **Comms studio** (`beanagile comms`, port 8802): messages, templates, writing checks, presentations and media.

Both run on their own. An [Odysseus](https://github.com/odysseus-dev/odysseus) hub is optional: when configured, the apps use it for documents, local models and scheduled jobs.

## Run

```bash
uv sync
uv run beanagile toolkit
```

Then open http://127.0.0.1:8801. The first visit asks you to set a password.

For development, `uv run beanagile toolkit --reload` restarts on code changes.

## Shared base (`src/beanagile/core`)

| Piece | What it does |
| --- | --- |
| Sign-in | One user per app: scrypt password, optional authenticator (TOTP), sessions in a hashed cookie, a throttle on failed sign-ins |
| Privacy levels | Every field is tagged private, presentable or exportable. Reads are filtered on the server; untagged fields count as private |
| Presentation mode | A per-session switch that hides private fields everywhere, for screen sharing |
| API tokens | Scoped tokens for LLM clients and the other app: `export:read`, `present:read`, `full`, plus app scopes such as `delivery:write` |
| Change log | Every data change records the field, old and new value, and who made it |
| Exports | One path that filters to exportable fields and logs what went out |
| UI shell | Navigation, routing, presentation toggle and a Settings screen for sign-in, tokens and history |

## Design system

Styles come from one Tailwind CSS v4 source, `src/beanagile/core/static/app.src.css`: design tokens (light and dark), base styles and the shared components. The built `app.css` is committed, so running the apps needs no build step. After editing the source, rebuild with:

```bash
./scripts/build-css.sh
```

The script uses Tailwind's standalone CLI from `.tools/` (not committed). Icons are a Lucide subset (`scripts/build_icons.py`), and the font is Inter; both are vendored with their licenses. Press ⌘K in either app for the command palette, or ? for keyboard shortcuts.

## Data

Data lives in `~/.beanagile/<app>/` (override with `BEANAGILE_DATA`). Nothing in this repository is real data; examples and samples are always marked `[Placeholder]`.

Optional Odysseus link: set `BEANAGILE_ODYSSEUS_URL` and `BEANAGILE_ODYSSEUS_TOKEN`.

## Test

```bash
uv run pytest
```

## License

MIT. See [LICENSE](LICENSE). Odysseus is a separate AGPL-3.0 project; these apps only talk to it over its API and include none of its code.
