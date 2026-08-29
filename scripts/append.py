#!/usr/bin/env python3
"""
Append a session's shots into data/shots.csv.

    python3 scripts/append.py 2026-09-01 export.csv
    python3 scripts/append.py 2026-09-01 export.csv --source screenshot_transcribed
    python3 scripts/append.py 2026-09-01 export.csv --force   # overwrite existing date

Maps common launch-monitor column names onto the schema, warns about
unrecognised columns instead of silently dropping them, and refuses to
write a session_date that already exists unless --force is passed.
"""

import argparse
import csv
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "data", "shots.csv")

SCHEMA = ["session_date", "session_id", "shot_no", "time", "club", "context", "hole",
          "shot_type", "exclude_from_stats", "exclude_reason",
          "carry_m", "total_m",
          "offline_m", "club_speed_kmh", "ball_speed_kmh", "smash",
          "spin_axis_deg", "back_spin_rpm", "side_spin_rpm", "launch_angle_deg",
          "launch_dir_deg", "face_angle_deg", "swing_path_deg", "face_to_path_deg",
          "aoa_deg", "dyn_loft_deg", "impact_w_mm", "impact_h_mm", "lie_deg",
          "closure_rate_dps", "source"]

# Loose matching: lowercased, non-alphanumerics stripped.
ALIASES = {
    "shot": "shot_no", "shotnumber": "shot_no", "shotno": "shot_no", "no": "shot_no",
    "date": "time", "datetime": "time", "timestamp": "time",
    "club": "club", "clubname": "club", "clubtype": "club",
    "carry": "carry_m", "carrym": "carry_m", "carrydistance": "carry_m",
    "distance": "total_m", "total": "total_m", "totalm": "total_m",
    "totaldistance": "total_m",
    "offline": "offline_m", "offlinem": "offline_m", "sidedistance": "offline_m",
    "clubspeed": "club_speed_kmh", "clubheadspeed": "club_speed_kmh",
    "ballspeed": "ball_speed_kmh",
    "smash": "smash", "smashfactor": "smash",
    "spinaxis": "spin_axis_deg",
    "backspin": "back_spin_rpm", "sidespin": "side_spin_rpm",
    "totalspin": None,  # recognised but not stored — derived from back+side
    "launchangle": "launch_angle_deg", "launchdir": "launch_dir_deg",
    "launchdirection": "launch_dir_deg",
    "faceangle": "face_angle_deg", "face": "face_angle_deg",
    "swingpath": "swing_path_deg", "path": "swing_path_deg",
    "facetopath": "face_to_path_deg",
    "aoa": "aoa_deg", "attackangle": "aoa_deg",
    "dynamicloft": "dyn_loft_deg", "loft": "dyn_loft_deg",
    "impactwidth": "impact_w_mm", "impactheight": "impact_h_mm",
    "lie": "lie_deg", "closurerate": "closure_rate_dps", "closure": "closure_rate_dps",
    "hole": "hole", "holenumber": "hole", "holeno": "hole", "context": "context",
    "shottype": "shot_type", "exclude": "exclude_from_stats",
    "excludefromstats": "exclude_from_stats", "excludereason": "exclude_reason",
}


def norm(name):
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def map_columns(fieldnames):
    mapping, unknown = {}, []
    for f in fieldnames:
        key = norm(f)
        if key in ALIASES:
            if ALIASES[key]:
                mapping[f] = ALIASES[key]
        elif key in {norm(c) for c in SCHEMA}:
            mapping[f] = next(c for c in SCHEMA if norm(c) == key)
        else:
            unknown.append(f)
    return mapping, unknown


def existing_sessions():
    """Existing session_ids — NOT dates. Two sessions can share a day
    (e.g. a warm-up block and then an SGT round)."""
    if not os.path.exists(SHOTS):
        return set()
    with open(SHOTS, newline="") as f:
        return {r.get("session_id") or r["session_date"] for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session_date", help="ISO date, e.g. 2026-09-01")
    ap.add_argument("input_csv")
    ap.add_argument("--source", default="csv_export")
    ap.add_argument("--context", default="practice",
                    choices=["practice", "sgt", "play", "drill"],
                    help="practice = training block; sgt = Simulator Golf Tour round; "
                         "play = casual round; drill = drill reps (EXCLUDED from all "
                         "stats, since partial swings would corrupt the averages).")
    ap.add_argument("--description", default="",
                    help="Human description of the session, e.g. "
                         "'SGT Tour Championship Round 1 front nine' or "
                         "'Keperra West casual with Amanda'. Required \u2014 a session "
                         "without one is unidentifiable a month later.")
    ap.add_argument("--suffix", default="",
                    help="Disambiguator when there is more than one session of the "
                         "same context on one day, e.g. 'r2'.")
    ap.add_argument("--hole", default="",
                    help="Hole number for a single-hole import (sgt/play contexts). "
                         "Otherwise supply a 'hole' column in the input CSV.")
    ap.add_argument("--force", action="store_true",
                    help="replace rows if this session_date already exists")
    args = ap.parse_args()

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.session_date):
        sys.exit(f"session_date must be YYYY-MM-DD, got {args.session_date!r}")

    if not args.description.strip():
        sys.exit("--description is required. Give the session a human label, e.g.\n"
                 "  --description 'SGT Tour Championship Round 1 front nine'\n"
                 "  --description 'Keperra West casual with Amanda'")

    session_id = f"{args.session_date}-{args.context}"
    if args.suffix:
        session_id += f"-{args.suffix}"

    if session_id in existing_sessions() and not args.force:
        sys.exit(f"Session {session_id} already exists in shots.csv. "
                 f"Pass --force to replace it, or --suffix to add a separate "
                 f"session on the same day.")

    with open(args.input_csv, newline="") as f:
        reader = csv.DictReader(f)
        mapping, unknown = map_columns(reader.fieldnames or [])
        if unknown:
            print(f"Ignoring unrecognised columns: {', '.join(unknown)}")
        if not mapping:
            sys.exit("No recognised columns found — check the input file.")

        new_rows = []
        for src in reader:
            row = {c: "" for c in SCHEMA}
            row["session_date"] = args.session_date
            row["session_id"] = session_id
            row["source"] = args.source
            row["context"] = args.context
            if not row.get("shot_type"):
                row["shot_type"] = "full"
            if args.hole:
                row["hole"] = args.hole
            for src_col, dest in mapping.items():
                row[dest] = (src.get(src_col) or "").strip()
            if any(row[c] for c in ("carry_m", "ball_speed_kmh", "club")):
                new_rows.append(row)

    if not new_rows:
        sys.exit("No shot rows found in the input file.")

    if args.context in ("sgt", "play"):
        missing = [r for r in new_rows if not (r.get("hole") or "").strip()]
        if missing:
            sys.exit(f"{len(missing)} on-course shots have no hole number. "
                     f"Pass --hole N, or include a 'hole' column, so the rows "
                     f"can join to rounds.json.")
    else:
        for r in new_rows:
            r["hole"] = ""

    # Load current file, dropping the target date if replacing.
    old = []
    if os.path.exists(SHOTS):
        shutil.copy(SHOTS, SHOTS + ".bak")
        with open(SHOTS, newline="") as f:
            old = [r for r in csv.DictReader(f)
                   if not (args.force and r.get("session_id") == session_id)]

    combined = old + new_rows
    combined.sort(key=lambda r: (r["session_date"], r.get("session_id") or "",
                                 str(r.get("time") or "")))

    with open(SHOTS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SCHEMA, restval="")
        w.writeheader()
        w.writerows(combined)

    clubs = sorted({r["club"] for r in new_rows if r["club"]})
    print(f"Added {len(new_rows)} shots to session {session_id}")
    print(f"  {args.description}")
    print(f"  clubs: {', '.join(clubs) if clubs else 'no club field'}")
    print(f"shots.csv now holds {len(combined)} rows. Backup at shots.csv.bak")
    print("Next: add a row to data/sessions.csv, then run scripts/build.py")


if __name__ == "__main__":
    main()
