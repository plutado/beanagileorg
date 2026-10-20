"""Writing checks run on every draft: placeholders left, plain language, long sentences, summary first, and wording about people.

All rule-based and local. A failed check that "blocks" stops a message from being marked ready.
"""

import re

from beanagileorg.core.sensitivity import check_text

# Common workplace jargon and a plainer alternative. Glossary terms added in the app extend this list.
JARGON = {
    "leverage": "use",
    "utilize": "use",
    "synergy": "working together",
    "bandwidth": "time",
    "circle back": "come back to",
    "touch base": "check in",
    "deep dive": "close look",
    "action item": "next step",
    "deliverable": "what we'll hand over",
    "going forward": "from now on",
    "low-hanging fruit": "quick win",
    "move the needle": "make a difference",
    "paradigm": "approach",
    "holistic": "complete",
    "best practice": "proven approach",
    "ecosystem": "set of tools",
    "stakeholder buy-in": "agreement",
    "socialize": "share",
    "operationalize": "put into practice",
    "net-net": "in short",
    "EOD": "end of day",
    "ETA": "expected date",
    "MVP": "first version",
    "KPI": "measure",
    "SLA": "service promise",
}

LONG_SENTENCE = 25
SUMMARY_WORDS = 50
PLACEHOLDER = re.compile(r"\[Placeholder[^\]]*\]", re.IGNORECASE)


def _prose(body: str) -> str:
    """Body text without headings, table rows, list markers or markdown emphasis."""
    lines = []
    for line in (body or "").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("|") or set(s) <= set("-|: "):
            lines.append("")
            continue
        s = re.sub(r"^([-*+]|\d+\.)\s+", "", s)
        lines.append(re.sub(r"[*_`]", "", s))
    return "\n".join(lines)


def _first_paragraph(body: str) -> str:
    for para in re.split(r"\n\s*\n", _prose(body)):
        if para.strip():
            return " ".join(para.split())
    return ""


def run_checks(body: str, glossary: list[dict] | None = None, people: dict | None = None) -> list[dict]:
    body = body or ""
    results = []

    found = sorted(set(m.group(0) for m in PLACEHOLDER.finditer(body)))
    results.append({
        "check": "placeholders",
        "label": "Placeholders left",
        "result": "fail" if found else "pass",
        "blocks": bool(found),
        "findings": [f"{p}" for p in found[:10]] + ([f"and {len(found) - 10} more"] if len(found) > 10 else []),
    })

    terms = dict(JARGON)
    for g in glossary or []:
        if g.get("term"):
            terms[g["term"]] = g.get("plain") or ""
    prose = _prose(body)
    hits = []
    for term, plain in sorted(terms.items()):
        flags = 0 if term.isupper() else re.IGNORECASE
        if re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", prose, flags):
            hits.append(f'"{term}"' + (f" → {plain}" if plain else ""))
    results.append({
        "check": "plain_language",
        "label": "Plain language",
        "result": "warn" if hits else "pass",
        "blocks": False,
        "findings": hits,
    })

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", prose) if s.strip()]
    long = [s for s in sentences if len(s.split()) > LONG_SENTENCE]
    results.append({
        "check": "long_sentences",
        "label": "Long sentences",
        "result": "warn" if long else "pass",
        "blocks": False,
        "findings": [f"{len(s.split())} words: {s[:90]}{'…' if len(s) > 90 else ''}" for s in long[:5]],
    })

    first = _first_paragraph(body)
    words = len(first.split())
    problem = "There's no opening summary." if not first else (
        f"The opening runs {words} words; aim for under {SUMMARY_WORDS} so the point lands first." if words > SUMMARY_WORDS else ""
    )
    results.append({
        "check": "summary_first",
        "label": "Summary first",
        "result": "warn" if problem else "pass",
        "blocks": False,
        "findings": [problem] if problem else [],
    })

    if people is not None:  # the scan context from core.sensitivity: names held here and your own word list
        found = check_text(body, people)
        warn = [f for f in (found or {}).get("findings", []) if f["level"] == "warn"]
        results.append({
            "check": "about_people",
            "label": "About people",
            "result": "warn" if warn else "pass",
            "blocks": False,
            "findings": list(dict.fromkeys(f'{f["reason"]} ({", ".join(f["words"][:3])}): {f["excerpt"][:90]}' for f in warn))[:5],
        })
    return results


def blocking(results: list[dict]) -> list[str]:
    return [r["label"] for r in results if r["blocks"] and r["result"] == "fail"]
