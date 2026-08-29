#!/usr/bin/env python3
"""
Publish the dashboard to GitHub Pages with a correct, automatic build stamp.

    GITHUB_TOKEN=... python3 scripts/publish.py path/to/dashboard.html

Why this exists: the "last updated" date was previously hand-written into the
HTML, which meant it went stale the moment anyone forgot. Two dates matter and
both are now derived, never typed:

  * "last activity"  — computed in the browser from the newest session OR round
                       in the data. Rounds count too; using sessions alone made
                       the header read 26 Aug when a round had been logged on
                       the 29th.
  * "Published"      — stamped into __BUILT_AT__ here, at publish time.

Uploads to index.html (the stable URL) and a versioned copy, then verifies the
stamp actually landed rather than trusting the API's 200.
"""

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

REPO = "StevenFay/golf"
API = f"https://api.github.com/repos/{REPO}/contents/"


def gh(path, method="GET", payload=None, token=None):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode() if payload else None,
        method=method,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def put(path, content_bytes, message, token):
    sha = (gh(path, token=token) or {}).get("sha")
    payload = {"message": message,
               "content": base64.b64encode(content_bytes).decode()}
    if sha:
        payload["sha"] = sha
    gh(path, "PUT", payload, token)
    print(f"  uploaded {path}")


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN in the environment.")
    src = sys.argv[1] if len(sys.argv) > 1 else "golf_dashboard.html"
    if not os.path.exists(src):
        sys.exit(f"No such file: {src}")

    html = open(src, encoding="utf-8").read()
    if "__BUILT_AT__" not in html:
        print("  WARNING: no __BUILT_AT__ placeholder found — stamp will be missing")

    stamp = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    stamped = html.replace("__BUILT_AT__", stamp).encode("utf-8")

    version = re.search(r"(v\d+)", os.path.basename(src))
    versioned = f"golf_dashboard_{version.group(1)}.html" if version else None

    print(f"Publishing {src} — stamp: {stamp}")
    put("index.html", stamped, f"Dashboard published {stamp}", token)
    if versioned:
        put(versioned, stamped, f"Versioned copy, {stamp}", token)

    # Verify: re-fetch and confirm the stamp is really there.
    live = gh("index.html", token=token)
    text = base64.b64decode(live["content"]).decode("utf-8", "replace")
    if stamp in text:
        print(f"  verified: published index.html carries the stamp")
    else:
        sys.exit("  FAILED: stamp not found in the published file")
    if "__BUILT_AT__" in text:
        sys.exit("  FAILED: placeholder still present in the published file")
    print("Done — https://stevenfay.github.io/golf/")


if __name__ == "__main__":
    main()
