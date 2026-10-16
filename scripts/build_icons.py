"""Build the icon sprite from a lucide-static package: only the icons the apps use.

Usage: python3 scripts/build_icons.py <path to lucide-static/package/icons>
Writes src/beanagileorg/core/static/vendor/icons.svg. Add a name to ICONS to make it available as BA.icon(name).
"""

import re
import sys
from pathlib import Path

ICONS = [
    # navigation
    "sun", "calendar-check", "users", "graduation-cap", "messages-square", "chart-column", "list-checks",
    "presentation", "siren", "user-round", "settings", "calendar-clock", "mail", "layout-template",
    "calendar-days", "send", "spell-check", "film", "handshake", "map", "grid-3x3", "triangle-alert", "gauge",
    "file-text", "notebook-pen", "refresh-ccw", "kanban", "thumbs-up", "flag", "building-2", "flask-conical", "play", "copy", "network", "external-link", "git-branch", "arrow-up", "arrow-down", "compass", "lightbulb", "notebook", "circle-help", "info", "wrench", "list-ordered", "arrow-big-up", "undo-2", "users-round",
    # interface
    "search", "command", "moon", "monitor", "x", "plus", "chevron-down", "chevron-right", "log-out",
    "eye-off", "eye", "keyboard", "check", "circle-alert", "sparkles", "inbox", "panel-left",
]

OUT = Path(__file__).resolve().parent.parent / "src/beanagileorg/core/static/vendor/icons.svg"


def main(icons_dir: str) -> None:
    src = Path(icons_dir)
    symbols = []
    for name in ICONS:
        svg = (src / f"{name}.svg").read_text()
        inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1).strip()
        inner = re.sub(r"\s+", " ", inner)
        symbols.append(f'<symbol id="{name}" viewBox="0 0 24 24">{inner}</symbol>')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n<!-- Lucide icons (ISC license), see LICENSE-lucide -->\n'
        + "\n".join(symbols)
        + "\n</svg>\n"
    )
    print(f"{len(symbols)} icons -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
