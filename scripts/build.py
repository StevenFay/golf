#!/usr/bin/env python3
"""
Regenerate derived summaries from data/shots.csv.

Everything in build/ is disposable — shots.csv is the source of truth.
Run after appending new sessions:

    python3 scripts/build.py

Outputs:
    build/club_summary.csv   per-club aggregates for the latest session and all-time
    build/club_trend.csv     per-club, per-session averages (for trend charts)
    build/dashboard_seed.js  BAG / DEEP constants ready to paste into the dashboard

Standard library only — no pandas required.
"""

import csv
import json
import os
import statistics as st
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
BUILD = os.path.join(ROOT, "build")

# Club order from longest to shortest — used for sorting output.
CLUB_ORDER = ["DR", "3W", "5W", "3H", "4H", "3I", "4I", "5I", "6I", "7I",
              "8I", "9I", "PW", "GW", "SW", "LW", "P"]

NUMERIC = ["carry_m", "total_m", "offline_m", "club_speed_kmh", "ball_speed_kmh",
           "smash", "spin_axis_deg", "back_spin_rpm", "side_spin_rpm",
           "launch_angle_deg", "launch_dir_deg", "face_angle_deg", "swing_path_deg",
           "face_to_path_deg", "aoa_deg", "dyn_loft_deg", "impact_w_mm",
           "impact_h_mm", "lie_deg", "closure_rate_dps"]


def load_shots():
    """Read shots.csv, coercing numeric columns and dropping blanks."""
    path = os.path.join(DATA, "shots.csv")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for col in NUMERIC:
            v = (r.get(col) or "").strip()
            r[col] = float(v) if v not in ("", "None") else None
    return rows


def club_key(club):
    return CLUB_ORDER.index(club) if club in CLUB_ORDER else 99


def agg(values):
    """min / mean / max for a list that may contain None."""
    vals = [v for v in values if v is not None]
    if not vals:
        return None, None, None
    return min(vals), st.mean(vals), max(vals)


def summarise(rows, label):
    """Per-club aggregates over the given rows."""
    by_club = defaultdict(list)
    for r in rows:
        by_club[r["club"]].append(r)

    out = []
    for club in sorted(by_club, key=club_key):
        shots = by_club[club]
        rec = {"scope": label, "club": club, "shots": len(shots)}
        for col, short in [("carry_m", "carry"), ("ball_speed_kmh", "ball"),
                           ("club_speed_kmh", "clubspd"), ("smash", "smash"),
                           ("offline_m", "offline"), ("back_spin_rpm", "backspin"),
                           ("side_spin_rpm", "sidespin"), ("face_angle_deg", "face"),
                           ("swing_path_deg", "path"), ("impact_h_mm", "impact_h"),
                           ("impact_w_mm", "impact_w"), ("lie_deg", "lie"),
                           ("closure_rate_dps", "closure")]:
            lo, avg, hi = agg([s[col] for s in shots])
            rec[f"{short}_min"] = round(lo, 2) if lo is not None else ""
            rec[f"{short}_avg"] = round(avg, 2) if avg is not None else ""
            rec[f"{short}_max"] = round(hi, 2) if hi is not None else ""
        out.append(rec)
    return out


def write_csv(path, rows):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {os.path.relpath(path, ROOT)} ({len(rows)} rows)")


def main():
    shots = load_shots()
    dates = sorted({r["session_date"] for r in shots})
    print(f"Loaded {len(shots)} shots across {len(dates)} sessions "
          f"({dates[0]} to {dates[-1]})")

    # All-time plus the most recent session.
    summary = summarise(shots, "all_time")
    latest = dates[-1]
    summary += summarise([r for r in shots if r["session_date"] == latest], latest)
    write_csv(os.path.join(BUILD, "club_summary.csv"), summary)

    # Per-club per-session averages, for trend lines.
    trend = []
    for d in dates:
        for rec in summarise([r for r in shots if r["session_date"] == d], d):
            trend.append({"session_date": d, "club": rec["club"],
                          "shots": rec["shots"], "carry_avg": rec["carry_avg"],
                          "ball_avg": rec["ball_avg"], "smash_avg": rec["smash_avg"],
                          "offline_avg": rec["offline_avg"],
                          "face_avg": rec["face_avg"]})
    write_csv(os.path.join(BUILD, "club_trend.csv"), trend)

    # Dashboard seed: BAG from the full-bag session, DEEP from the newest 7I block.
    bag_date = max(
        dates,
        key=lambda d: len({r["club"] for r in shots if r["session_date"] == d})
    )
    bag_rows = summarise([r for r in shots if r["session_date"] == bag_date], bag_date)
    bag = [{"club": r["club"], "n": r["shots"],
            "carry": [r["carry_min"], r["carry_avg"], r["carry_max"]],
            "ball": [r["ball_min"], r["ball_avg"], r["ball_max"]],
            "cs": r["clubspd_avg"],
            "smash": [r["smash_min"], r["smash_avg"], r["smash_max"]],
            "off": r["offline_avg"], "back": r["backspin_avg"]} for r in bag_rows]

    seven = [r for r in shots if r["club"] == "7I"]
    seven_latest = max({r["session_date"] for r in seven}) if seven else None
    deep_rows = [r for r in seven if r["session_date"] == seven_latest]
    deep = summarise(deep_rows, seven_latest)[0] if deep_rows else {}

    os.makedirs(BUILD, exist_ok=True)
    seed_path = os.path.join(BUILD, "dashboard_seed.js")
    with open(seed_path, "w") as f:
        f.write("// Generated by scripts/build.py — do not edit by hand.\n")
        f.write(f"// Bag from session {bag_date}; 7-iron deep dive from {seven_latest}.\n")
        f.write("const BAG = " + json.dumps(bag, indent=2) + ";\n\n")
        f.write("const DEEP_RAW = " + json.dumps(deep, indent=2) + ";\n")
    print(f"  wrote {os.path.relpath(seed_path, ROOT)}")

    # Quick console read-out of the current focus metric.
    if deep_rows:
        faces = [r["face_angle_deg"] for r in deep_rows if r["face_angle_deg"] is not None]
        if faces:
            print(f"\n7-iron face angle ({seven_latest}): "
                  f"avg {st.mean(faces):+.1f}°, "
                  f"{sum(1 for v in faces if 0 <= v <= 3)}/{len(faces)} shots in the 0–3° target band")


if __name__ == "__main__":
    main()
