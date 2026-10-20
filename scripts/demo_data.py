"""Fill a running toolkit with placeholder demo data for screenshots and demos.

Every value is bracketed placeholder text. Run it against a scratch instance, never your real data:

    BEANAGILEORG_DATA=/tmp/ba-demo .venv/bin/beanagileorg toolkit &
    python scripts/demo_data.py http://127.0.0.1:8801 '<password>'

On a fresh instance it sets the password first; otherwise it signs in with it.
"""

import http.cookiejar
import json
import sys
import urllib.request
from datetime import date, timedelta
from urllib.parse import urlencode

BASE, PASSWORD = sys.argv[1].rstrip("/"), sys.argv[2]
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
