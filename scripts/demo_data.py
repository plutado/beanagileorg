"""Fill a running toolkit with placeholder demo data for screenshots and demos.

Every value is bracketed placeholder text. Run it against a scratch instance, never your real data:

    BEANAGILEORG_DATA=/tmp/ba-demo .venv/bin/beanagileorg toolkit &
    python scripts/demo_data.py http://127.0.0.1:8801 '<password>' /tmp/ba-demo/toolkit/toolkit.db

On a fresh instance it sets the password first; otherwise it signs in with it. The optional database path lets it
backdate the change log, so the finished Sprint 1 has a day-by-day history for its burndown.
"""

import http.cookiejar
import json
import sqlite3
import sys
import urllib.request
from datetime import date, timedelta
from urllib.parse import urlencode

BASE, PASSWORD = sys.argv[1].rstrip("/"), sys.argv[2]
DB = sys.argv[3] if len(sys.argv) > 3 else None
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def form(path, data):
    opener.open(urllib.request.Request(BASE + path, urlencode(data).encode(), method="POST"))


def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={"Content-Type": "application/json"})
    with opener.open(req) as r:
        text = r.read()
        return json.loads(text) if text else None


def day(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


try:
    form("/setup", {"password": PASSWORD, "confirm": PASSWORD})
except Exception:
    pass
form("/login", {"password": PASSWORD})

api("POST", "/api/seed-placeholders")
api("PUT", "/api/toolkit/settings", {"start_date": day(-39)})
people = [p["id"] for p in api("GET", "/api/people")]
me = api("POST", "/api/people", {"name": "[Placeholder you]", "active": True})["id"]
api("PUT", "/api/people/me", {"person_id": me})
p = lambda i: people[i % len(people)]
for n, pid in enumerate(people, 1):  # short names keep diagrams and boards readable
    api("PATCH", f"/api/people/{pid}", {"name": f"[Name {n}]"})
for title, due in (("[Placeholder task 1]", 0), ("[Placeholder task 2]", 0), ("[Placeholder task 3]", 1), ("[Placeholder task 4]", -2)):
    api("POST", "/api/tasks", {"title": title, "due": day(due)})
plan = api("GET", "/api/plans")[0]["id"]
for title, due, status, win in (("[Placeholder plan item 1]", 20, "done", False), ("[Placeholder plan item 2]", 45, "in progress", True),
                                ("[Placeholder plan item 3]", 60, "planned", False), ("[Placeholder plan item 4]", 85, "planned", True)):
    api("POST", "/api/plan-items", {"plan_id": plan, "title": title, "due_day": due, "status": status, "early_win": win})

# ---- a Planning Interval: five sprints, the last an Innovation and Planning sprint
pi = api("POST", "/api/program-increments", {"number": 1, "start_date": day(-3), "end_date": day(66),
                                              "objectives": "[Placeholder PI theme]"})["id"]
sprints = {s["number"]: s["id"] for s in api("GET", "/api/sprints")}
api("PATCH", f"/api/sprints/{sprints[2]}", {"pi_id": pi})
for n in (3, 4, 5, 6):
    start = 11 + (n - 3) * 14
    sprints[n] = api("POST", "/api/sprints", {"number": n, "start_date": day(start), "end_date": day(start + 13), "pi_id": pi,
                                              "goal": f"[Placeholder sprint goal {n}]",
                                              "kind": "innovation and planning" if n == 6 else "development"})["id"]

for i, (title, kind, value) in enumerate([("[Placeholder objective 1]", "committed", 10), ("[Placeholder objective 2]", "committed", 8),
                                           ("[Placeholder objective 3]", "committed", 8), ("[Placeholder objective 4]", "committed", 5),
                                           ("[Placeholder stretch objective]", "stretch", 3)]):
    api("POST", "/api/pi-objectives", {"pi_id": pi, "title": title, "kind": kind, "value_planned": value, "owner_id": p(i),
                                       "status": "in progress" if i < 2 else "not started"})

epics = [api("POST", "/api/epics", {"title": f"[Placeholder epic {n}]", "priority": pr})["id"] for n, pr in ((1, "high"), (2, "medium"))]
features = []
for i, pr in enumerate(("highest", "high", "high", "medium", "medium", "low")):
    features.append(api("POST", "/api/features", {"pi_id": pi, "epic_id": epics[i % 2], "title": f"[Placeholder feature {i + 1}]",
                                                  "priority": pr, "owner_id": p(i), "ticket_key": f"ABC-{200 + i}",
                                                  "status": "in progress" if i < 2 else "not started"})["id"])
story = 300
for i, f in enumerate(features):
    for k, n in enumerate((2, 3, 4, 5)[i % 2: i % 2 + 3]):
        story += 1
        api("POST", "/api/stories", {"feature_id": f, "sprint_id": sprints[n], "title": f"[Placeholder story {story - 300}]",
                                     "points": (3, 5, 8, 2, 3, 5)[(i + k) % 6], "owner_id": p(i + k), "ticket_key": f"ABC-{story}",
                                     "status": "done" if n == 2 and k == 0 else "not started"})

api("POST", "/api/dependencies", {"pi_id": pi, "feature_id": features[2], "depends_on_id": features[0], "team": "[Placeholder team B]",
                                  "description": "[Placeholder dependency 1]", "needed_by_id": sprints[3]})
api("POST", "/api/dependencies", {"pi_id": pi, "feature_id": features[4], "team": "[Placeholder platform team]",
                                  "description": "[Placeholder dependency 2]", "needed_by_id": sprints[4], "status": "at risk"})
api("POST", "/api/pi-milestones", {"pi_id": pi, "title": "[Placeholder release window]", "date": day(38), "kind": "release"})
api("POST", "/api/pi-milestones", {"pi_id": pi, "title": "[Placeholder peak-season freeze]", "date": day(52), "kind": "freeze"})
for title, roam, i in (("[Placeholder risk 1]", "owned", 0), ("[Placeholder risk 2]", "mitigated", 1),
                       ("[Placeholder risk 3]", "accepted", 2), ("[Placeholder risk 4]", "unroamed", 3)):
    api("POST", "/api/pi-risks", {"pi_id": pi, "title": title, "roam": roam, "owner_id": p(i)})
api("POST", f"/api/pis/{pi}/confidence", {"votes": [4, 4, 5, 3, 4, 4, 5]})

# ---- a finished Sprint 1: committed, one story added mid-sprint, stories done across the two weeks, one carried over
api("POST", "/api/backlog/paste", {"text": "\n".join(f"ABC-{100 + n} [Placeholder sprint 1 story {n}] | {pts}"
                                                      for n, pts in enumerate((3, 5, 2, 8, 3, 5, 2, 3), 1))})
s1_items = {i["jira_key"]: i["id"] for i in api("GET", "/api/backlog-items") if (i.get("jira_key") or "").startswith("ABC-10")}
s1_keys = [f"ABC-{100 + n}" for n in range(1, 9)]
for key in s1_keys:
    api("PATCH", f"/api/backlog-items/{s1_items[key]}", {"status": "ready"})
for key in s1_keys[:7]:
    api("POST", f"/api/sprint-planning/{sprints[1]}/pull", {"item_id": s1_items[key]})
api("POST", f"/api/sprint-planning/{sprints[1]}/commit", {})
api("POST", f"/api/sprint-planning/{sprints[1]}/pull", {"item_id": s1_items[s1_keys[7]]})  # added mid-sprint
done_on = {s1_keys[0]: 1, s1_keys[2]: 2, s1_keys[1]: 4, s1_keys[4]: 5, s1_keys[3]: 7, s1_keys[7]: 8, s1_keys[5]: 9}
for key in done_on:
    api("PATCH", f"/api/backlog-items/{s1_items[key]}", {"status": "done"})
if DB:
    s1 = next(s for s in api("GET", "/api/sprints") if s["number"] == 1)
    d, s1_days = date.fromisoformat(s1["start_date"]), []
    while d.isoformat() <= s1["end_date"]:
        if d.weekday() < 5:
            s1_days.append(d.isoformat())
        d += timedelta(days=1)
    before = (date.fromisoformat(s1["start_date"]) - timedelta(days=1)).isoformat()
    conn = sqlite3.connect(DB)
    def stamp(key, day, where):
        conn.execute(f"UPDATE change_log SET at = ? WHERE entity = 'backlog_item' AND record_id = ? AND {where}", (f"{day} 12:00:00", str(s1_items[key])))
    for key in s1_keys:
        joined = s1_days[3] if key == s1_keys[7] else before
        stamp(key, before, "NOT (field IN ('sprint_id', 'status'))")
        stamp(key, before, "field = 'status' AND new_value IN ('needs refinement', 'ready')")
        stamp(key, joined, "(field = 'sprint_id' OR (field = 'status' AND new_value = 'in sprint'))")
        if key in done_on:
            stamp(key, s1_days[done_on[key]], "field = 'status' AND new_value = 'done'")
    conn.commit()
    conn.close()
api("POST", f"/api/sprint-planning/{sprints[1]}/close", {})
api("PUT", "/api/planning/product-goal", {"text": "[Placeholder product goal]"})

# ---- the sprint backlog beside Jira: refined, estimated, four stories pulled into the current sprint
api("POST", "/api/backlog/paste", {"text": "\n".join(f"ABC-{120 + n} [Placeholder backlog story {n}] | {(3, 5, 2, 8, 3, 5, 3, 2)[n - 1]}" for n in range(1, 9))})
backlog = api("GET", "/api/backlog")
items = backlog["items"] if isinstance(backlog, dict) else backlog
for k, item in enumerate(items):
    if k < 6:
        api("PATCH", f"/api/backlog-items/{item['id']}", {"status": "ready"})
    if k < 4:
        api("POST", f"/api/sprint-planning/{sprints[2]}/pull", {"item_id": item["id"]})

# the Sprint 1 review's feedback, added after the backlog is refined so it waits to be refined itself
api("POST", f"/api/sprint-planning/{sprints[1]}/review/feedback", {"text": "[Placeholder stakeholder request from the review]", "from": "[Name 4]"})

# ---- the portfolio: two strategic themes and epics across the Kanban, including the PI's own epics
themes = [api("POST", "/api/strategic-themes", {"name": f"[Placeholder theme {n}]", "objective": f"[Placeholder measurable objective {n}]"})["id"] for n in (1, 2)]
case = lambda n: {"hypothesis": f"[Placeholder hypothesis {n}]", "outcomes": f"[Placeholder outcomes {n}]",
                  "leading_indicators": f"[Placeholder leading indicators {n}]", "mvp": f"[Placeholder MVP {n}]", "mvp_estimate": "[Placeholder estimate]"}
api("PATCH", f"/api/epics/{epics[0]}", {**case(1), "theme_id": themes[0], "owner_id": p(1), "kanban_state": "implementing MVP",
                                         "business_value": 13, "time_criticality": 8, "risk_reduction": 5, "job_size": 8})
api("PATCH", f"/api/epics/{epics[1]}", {**case(2), "theme_id": themes[1], "owner_id": p(2), "kanban_state": "implementing persevere",
                                         "decision": "persevere", "decision_date": day(-20), "decision_notes": "[Placeholder: what the leading indicators showed]"})
for n, (state, theme, kind, scores, with_case) in enumerate((("funnel", None, "business", None, False), ("reviewing", 0, "business", None, False),
                                                             ("analyzing", 1, "enabler", (5, 3, 13, 5), False), ("ready", 0, "business", (8, 13, 3, 5), True),
                                                             ("ready", 1, "enabler", (3, 5, 8, 2), True), ("done", 0, "business", None, True)), 3):
    body = {"title": f"[Placeholder epic {n}]", "epic_type": kind, "kanban_state": state, "theme_id": themes[theme] if theme is not None else None}
    if scores:
        body.update(dict(zip(("business_value", "time_criticality", "risk_reduction", "job_size"), scores)))
    if with_case:
        body.update(case(n))
    if state == "done":
        body.update({"decision": "stop", "decision_date": day(-45), "decision_notes": "[Placeholder: why it stopped]"})
    api("POST", "/api/epics", body)

# ---- the Agile Release Train: roles, the team, the PI, and an ART backlog scored by WSJF
art = api("POST", "/api/arts", {"name": "[Placeholder train]", "mission": "[Placeholder train mission]", "rte_id": p(1),
                                "product_manager_id": p(2), "architect_id": p(3), "business_owner_ids": [p(4), p(5)]})["id"]
for team in api("GET", "/api/teams"):
    api("PATCH", f"/api/teams/{team['id']}", {"art_id": art})
api("PATCH", f"/api/program-increments/{pi}", {"art_id": art})
for f in features:
    api("PATCH", f"/api/features/{f}", {"art_id": art})
for n, (kind, bv, tc, rr, size) in enumerate((("business", 13, 8, 5, 5), ("enabler", 5, 8, 13, 3), ("business", 8, 3, 2, 8),
                                              ("business", 20, 13, 3, 13), ("enabler", 3, 2, 8, 2)), 1):
    api("POST", "/api/features", {"title": f"[Placeholder next-PI feature {n}]", "art_id": art, "feature_type": kind,
                                  "business_value": bv, "time_criticality": tc, "risk_reduction": rr, "job_size": size})

# ---- an alliance plan with an influence diagram
stances = ("champion", "supporter", "supporter", "neutral", "skeptic", "blocker")
for i, s in enumerate(stances):
    api("PATCH", f"/api/people/{p(i)}", {"stance": s, "influence": ("high", "medium", "low")[i % 3], "opinion_leader": i in (0, 4)})
plan_stance = {"champion": "for", "supporter": "for", "neutral": "undecided", "skeptic": "undecided", "blocker": "against"}
rows = [{"person_id": p(i), "what": f"[Placeholder ask {i + 1}]", "when": day(14 + i * 3), "stance": plan_stance[s]} for i, s in enumerate(stances)]
api("POST", "/api/alliance-plans", {"title": "[Placeholder early win]", "objective": "[Placeholder objective for the win]",
                                    "rows": {"rows": rows}, "winning_ids": [p(0), p(1), p(2)], "blocking_ids": [p(5)]})
for a, b, strength in ((0, 3, 3), (1, 4, 2), (2, 3, 1), (4, 5, 3), (0, 1, 2), (3, 5, 1), (6, 4, 2)):
    api("POST", "/api/influence-links", {"from_id": p(a), "to_id": p(b), "strength": strength, "topic": f"[Placeholder topic {a + 1}]"})

# ---- the current 90-day cycle, lined up with the PI
cycle = api("GET", "/api/cycles/overview")["cycles"][0]["id"]
api("PATCH", f"/api/cycles/{cycle}", {"focus": "[Placeholder cycle focus]", "pi_id": pi,
                                      "goals": ["[Placeholder cycle goal 1]", "[Placeholder cycle goal 2]", "[Placeholder cycle goal 3]"]})

# ---- how far the organization practices SAFe and Scrum
for key, status in (("art", "partly"), ("pi", "practiced"), ("pi-planning", "practiced"), ("pi-objectives", "practiced"),
                    ("iteration", "practiced"), ("ip-iteration", "partly"), ("art-sync", "practiced"), ("system-demo", "partly"),
                    ("inspect-adapt", "not yet"), ("rte", "partly"), ("product-management", "partly"), ("business-owners", "practiced"), ("system-architect", "partly"), ("solution-train", "not used here"), ("sprint", "practiced"), ("daily-scrum", "practiced"),
                    ("sprint-review", "partly"), ("retrospective", "practiced"), ("definition-of-done", "partly")):
    try:
        api("PUT", f"/api/agile/practice/{key}", {"status": status})
    except Exception:
        pass

# ---- a new team member's own onboarding page, shared through a timed link with an access code
newbie = api("POST", "/api/people", {"name": "[Placeholder new hire]", "active": True, "manager_id": me})["id"]
try:
    api("POST", "/api/onboarding/starter")
except Exception:
    pass
ob = api("POST", "/api/onboardings", {"person_id": newbie})["id"]
api("PUT", "/api/share-base-url", {"base_url": BASE})
api("POST", f"/api/onboardings/{ob}/links", {})
for kind, text in (("win", "[Placeholder win]"), ("decision", "[Placeholder decision]"), ("blocker", "[Placeholder blocker]")):
    try:
        api("POST", "/api/log-entries", {"date": day(0), "kind": kind, "text": text})
    except Exception:
        pass
print("Demo data loaded.")
