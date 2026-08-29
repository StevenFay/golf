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

ID_COLS = ["session_id", "description"]

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


def check_descriptions(shots):
    """Every session_id in shots.csv should have a description in sessions.csv.

    A session without a human label is unidentifiable a month later, so this
    warns rather than letting it slip through silently.
    """
    path = os.path.join(DATA, "sessions.csv")
    described = {}
    if os.path.exists(path):
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                described[r.get("session_id", "")] = (r.get("description") or "").strip()
    rounds_path = os.path.join(DATA, "rounds.json")
    if os.path.exists(rounds_path):
        with open(rounds_path) as f:
            for r in json.load(f).get("rounds", []):
                described[r.get("session_id", "")] = (r.get("description") or "").strip()

    seen = {r.get("session_id") or "" for r in shots}
    for sid in sorted(seen):
        if not described.get(sid):
            print(f"  WARNING session {sid or '(blank)'} has no description "
                  f"— add one to sessions.csv")


def check_round_join(shots):
    """Warn if round shots don't line up with rounds.json.

    `hole` is only meaningful for on-course contexts (sgt, play), and must match a hole
    that actually exists in that date's round — otherwise the join silently
    drops shots and nobody notices.
    """
    path = os.path.join(DATA, "rounds.json")
    if not os.path.exists(path):
        return
    with open(path) as f:
        rounds = json.load(f).get("rounds", [])
    by_date = {r["date"]: {h["hole"] for h in r.get("holes", [])} for r in rounds}

    ROUND_CTX = ("sgt", "play")
    problems = []
    for r in shots:
        ctx, hole = (r.get("context") or "practice"), (r.get("hole") or "").strip()
        if ctx in ROUND_CTX:
            if not hole:
                problems.append(f"{r['session_date']} shot {r['shot_no']}: "
                                f"context={ctx} but no hole")
            elif r["session_date"] not in by_date:
                problems.append(f"{r['session_date']}: round shots but no "
                                f"matching round in rounds.json")
            elif int(float(hole)) not in by_date[r["session_date"]]:
                problems.append(f"{r['session_date']} hole {hole}: not in "
                                f"that round's holes")
        elif hole:
            problems.append(f"{r['session_date']} shot {r['shot_no']}: "
                            f"hole set but context={ctx}")

    for p in sorted(set(problems))[:10]:
        print(f"  WARNING {p}")
    if len(set(problems)) > 10:
        print(f"  ... and {len(set(problems)) - 10} more")


def main():
    shots = load_shots()
    dates = sorted({r["session_date"] for r in shots})
    contexts = sorted({r.get("context") or "practice" for r in shots})
    print(f"Loaded {len(shots)} shots across {len(dates)} sessions "
          f"({dates[0]} to {dates[-1]}); contexts: {', '.join(contexts)}")

    # All data is simulator data. Contexts:
    #   practice - training / block work
    #   sgt      - Simulator Golf Tour competitive rounds
    #   play     - general casual rounds
    #   drill    - drill reps (half speed, shortened swings) — EXCLUDED from stats,
    #              because deliberately partial swings would corrupt every average.
    def excluded(r):
        """Drill sessions, plus any individually flagged shot.

        Per-shot exclusion exists for swings that were never meant to be full:
        punch-outs from trees, deliberate knockdowns, stymied recoveries. They
        are real golf and belong in the round, but pooling them into club
        averages misrepresents what the club does.
        """
        if (r.get("context") or "practice") == "drill":
            return True
        return str(r.get("exclude_from_stats") or "").strip().lower() in ("1", "true", "yes", "y")

    rng = [r for r in shots if not excluded(r)]
    drills = [r for r in shots if (r.get("context") or "practice") == "drill"]
    flagged = [r for r in shots if excluded(r) and (r.get("context") or "practice") != "drill"]
    if flagged:
        print(f"  {len(flagged)} shot(s) individually excluded from stats:")
        for r in flagged[:6]:
            print(f"    {r['session_date']} shot {r['shot_no']} {r.get('club','')}"
                  f" — {r.get('exclude_reason') or 'no reason given'}")
    by_ctx = defaultdict(list)
    for r in shots:
        by_ctx[r.get("context") or "practice"].append(r)
    print("  by context: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(by_ctx.items())))
    if drills:
        print(f"  {len(drills)} drill shots excluded from all stats")
    check_round_join(shots)
    check_descriptions(shots)

    # All-time (everything but drills), plus the most recent session.
    summary = summarise(rng, "all_time")
    latest = dates[-1]
    summary += summarise([r for r in rng if r["session_date"] == latest], latest)
    # Per-context scopes too, so practice vs on-course can still be compared
    # without the headline numbers being split.
    for ctx in ("practice", "sgt", "play", "drill"):
        if by_ctx.get(ctx):
            summary += summarise(by_ctx[ctx], f"context_{ctx}")
    write_csv(os.path.join(BUILD, "club_summary.csv"), summary)

    # Per-club per-session averages, for trend lines. Context kept as a column
    # so a chart can filter or split on it rather than silently averaging both.
    trend = []
    for d in dates:
        for ctx in sorted(by_ctx):
            day = [r for r in by_ctx[ctx] if r["session_date"] == d]
            for rec in summarise(day, d):
                trend.append({"session_date": d, "context": ctx,
                              "club": rec["club"],
                              "shots": rec["shots"], "carry_avg": rec["carry_avg"],
                              "ball_avg": rec["ball_avg"], "smash_avg": rec["smash_avg"],
                              "offline_avg": rec["offline_avg"],
                              "face_avg": rec["face_avg"]})
    write_csv(os.path.join(BUILD, "club_trend.csv"), trend)

    # Dashboard seed: BAG from the widest non-drill session, DEEP from newest 7I block.
    bag_date = max(
        dates,
        key=lambda d: len({r["club"] for r in rng if r["session_date"] == d})
    )
    bag_rows = summarise([r for r in rng if r["session_date"] == bag_date], bag_date)
    bag = [{"club": r["club"], "n": r["shots"],
            "carry": [r["carry_min"], r["carry_avg"], r["carry_max"]],
            "ball": [r["ball_min"], r["ball_avg"], r["ball_max"]],
            "cs": r["clubspd_avg"],
            "smash": [r["smash_min"], r["smash_avg"], r["smash_max"]],
            "off": r["offline_avg"], "back": r["backspin_avg"]} for r in bag_rows]

    seven = [r for r in rng if r["club"] == "7I"]
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
