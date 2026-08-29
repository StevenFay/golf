#!/usr/bin/env python3
"""
Render the dashboard from generated data.

    python3 scripts/build.py                       # regenerate build/dashboard_data.json
    python3 scripts/render_dashboard.py TEMPLATE   # inject it -> build/dashboard.html

The dashboard template carries two placeholders:

    __DASHBOARD_DATA__   replaced with the JSON payload from build/dashboard_data.json
    __BUILT_AT__         replaced by scripts/publish.py at publish time

Everything the dashboard displays — the bag, the face-angle table, the deep
dive, trends, surfaces, session and round cards — comes from that payload,
which is derived from shots.csv honouring drill/putt/punch-out exclusions.

The ONLY hand-written content left in the template is the coaching narrative
in FOCUS (the diagnosis and the drill list), which is judgement rather than
data and has no source to derive from.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAYLOAD = os.path.join(ROOT, "build", "dashboard_data.json")
OUT = os.path.join(ROOT, "build", "dashboard.html")


def main():
    template = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dashboard_template.html")
    if not os.path.exists(template):
        sys.exit(f"No template at {template}")
    if not os.path.exists(PAYLOAD):
        sys.exit("No build/dashboard_data.json — run scripts/build.py first.")

    html = open(template, encoding="utf-8").read()
    if "__DASHBOARD_DATA__" not in html:
        sys.exit("Template has no __DASHBOARD_DATA__ placeholder — it is not data-driven.")

    payload = json.load(open(PAYLOAD))
    rendered = html.replace("__DASHBOARD_DATA__", json.dumps(payload, separators=(",", ":")))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"Rendered {os.path.relpath(OUT, ROOT)}")
    print(f"  {len(payload['trend'])} trend points, {len(payload['bag'])} clubs, "
          f"{len(payload['face_rows'])} face rows, {len(payload['rounds'])} rounds")
    if payload.get("sessions_without_shot_rows"):
        print("  NOTE no shot-level rows for: "
              + ", ".join(payload["sessions_without_shot_rows"])
              + " — these will not appear in trends or club stats.")


if __name__ == "__main__":
    main()
