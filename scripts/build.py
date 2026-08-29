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
from datetime import datetime, timezone
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


SURFACES = ("tee", "fairway", "rough", "deep_rough", "sand", "green", "recovery")


def surface_report(shots):
    """Break on-course shots down by the surface they were played from.

    NOTE: the strike is always off the same flat mat, so *delivery* data
    (club speed, face, path, smash, impact) is comparable regardless of
    surface. What differs is intent — a shot from deep rough is often a
    deliberate hack-out — and GSPro's penalised `carry_game_m`, which is
    NOT comparable across surfaces. Compare carry_m (measured) for the
    swing; compare carry_game_m only within the same surface.
    """
    on_course = [r for r in shots if (r.get("context") or "") in ("sgt", "play")]
    if not on_course:
        return
    by_surface = defaultdict(list)
    for r in on_course:
        by_surface[(r.get("surface") or "unrecorded")].append(r)
    print("  on-course shots by surface: " +
          ", ".join(f"{k}={len(v)}" for k, v in sorted(by_surface.items())))
    unknown = [k for k in by_surface if k not in SURFACES and k != "unrecorded"]
    if unknown:
        print(f"  WARNING unrecognised surface values: {', '.join(sorted(unknown))}")


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
    surface_report(shots)

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

    payload = dashboard_payload(shots)
    ppath = os.path.join(BUILD, "dashboard_data.json")
    with open(ppath, "w") as f:
        json.dump(payload, f, indent=1)
    print(f"  wrote {os.path.relpath(ppath, ROOT)} "
          f"({len(payload['trend'])} trend points, {len(payload['bag'])} clubs, "
          f"{len(payload['face_rows'])} face rows)")
    if payload["sessions_without_shot_rows"]:
        print("  NOTE sessions with no shot-level rows yet: "
              + ", ".join(payload["sessions_without_shot_rows"]))

    # Quick console read-out of the current focus metric.
    if deep_rows:
        faces = [r["face_angle_deg"] for r in deep_rows if r["face_angle_deg"] is not None]
        if faces:
            print(f"\n7-iron face angle ({seven_latest}): "
                  f"avg {st.mean(faces):+.1f}°, "
                  f"{sum(1 for v in faces if 0 <= v <= 3)}/{len(faces)} shots in the 0–3° target band")




# --------------------------------------------------------------------------
# Dashboard payload
# --------------------------------------------------------------------------
# Everything the dashboard renders is derived here, from shots.csv /
# sessions.csv / rounds.json. Nothing in the dashboard is hand-typed, because
# hand-typed constants silently go stale — that happened three times before
# this generator existed.

NON_SWING_CLUBS = {"P", "PUTTER", "PUTT"}


def is_swing(r):
    """Exclude putts and anything flagged out of stats."""
    if (r.get("club") or "").upper() in NON_SWING_CLUBS:
        return False
    if (r.get("context") or "practice") == "drill":
        return False
    return str(r.get("exclude_from_stats") or "").strip().lower() not in ("1", "true", "yes", "y")


def dashboard_payload(shots):
    swings = [r for r in shots if is_swing(r)]

    def vals(rs, col):
        return [r[col] for r in rs if r.get(col) is not None]

    def block(rs):
        f = vals(rs, "face_angle_deg")
        c = vals(rs, "carry_m")
        s = vals(rs, "smash")
        return {
            "n": len(rs),
            "face_avg": round(st.mean(f), 2) if f else None,
            "face_sd": round(st.stdev(f), 2) if len(f) > 1 else None,
            "face_band": sum(1 for v in f if 0 <= v <= 3) if f else None,
            "face_n": len(f),
            "face_closed": sum(1 for v in f if v < 0) if f else None,
            "carry_avg": round(st.mean(c), 1) if c else None,
            "smash_avg": round(st.mean(s), 2) if s else None,
        }

    # per session-and-club face blocks (the face-angle table)
    face_rows = []
    for sid in sorted({r.get("session_id") or r["session_date"] for r in swings}):
        rs = [r for r in swings if (r.get("session_id") or r["session_date"]) == sid]
        by_club = defaultdict(list)
        for r in rs:
            by_club[r["club"]].append(r)
        main = max(by_club.items(), key=lambda kv: len(kv[1]))
        b = block(main[1])
        if b["face_avg"] is None:
            continue
        face_rows.append({"session_id": sid, "date": rs[0]["session_date"],
                          "club": main[0], "context": rs[0].get("context") or "practice", **b})

    # trend series, one point per session (all swing clubs pooled)
    trend = []
    for d in sorted({r["session_date"] for r in swings}):
        rs = [r for r in swings if r["session_date"] == d]
        b = block(rs)
        trend.append({"date": d, "n": b["n"], "face_avg": b["face_avg"],
                      "face_sd": b["face_sd"], "smash_avg": b["smash_avg"]})

    # the bag: widest-coverage session
    dates = sorted({r["session_date"] for r in swings})
    bag_date = max(dates, key=lambda d: len({r["club"] for r in swings if r["session_date"] == d}))
    bag = []
    for club in sorted({r["club"] for r in swings if r["session_date"] == bag_date}, key=club_key):
        rs = [r for r in swings if r["session_date"] == bag_date and r["club"] == club]
        lo, avg, hi = agg(vals(rs, "carry_m"))
        blo, bavg, bhi = agg(vals(rs, "ball_speed_kmh"))
        slo, savg, shi = agg(vals(rs, "smash"))
        _, cs, _ = agg(vals(rs, "club_speed_kmh"))
        _, off, _ = agg(vals(rs, "offline_m"))
        _, back, _ = agg(vals(rs, "back_spin_rpm"))
        bag.append({"club": club, "n": len(rs),
                    "carry": [lo, round(avg, 1), hi] if avg is not None else None,
                    "ball": [blo, round(bavg, 1), bhi] if bavg is not None else None,
                    "cs": round(cs, 1) if cs is not None else None,
                    "smash": [slo, round(savg, 2), shi] if savg is not None else None,
                    "off": round(off, 1) if off is not None else None,
                    "back": round(back) if back is not None else None})

    # deep dive: newest session's biggest club block
    latest = dates[-1]
    rs = [r for r in swings if r["session_date"] == latest]
    by_club = defaultdict(list)
    for r in rs:
        by_club[r["club"]].append(r)
    dclub, drows = max(by_club.items(), key=lambda kv: len(kv[1]))
    METRICS = [("face_angle_deg", "Face angle", "\u00b0"), ("face_to_path_deg", "Face to path", "\u00b0"),
               ("swing_path_deg", "Swing path", "\u00b0"), ("side_spin_rpm", "Side spin", " rpm"),
               ("offline_m", "Off line", " m"), ("spin_axis_deg", "Spin axis", "\u00b0"),
               ("smash", "Smash factor", ""), ("carry_m", "Carry", " m"),
               ("ball_speed_kmh", "Ball speed", ""), ("club_speed_kmh", "Club speed", ""),
               ("aoa_deg", "Attack angle", "\u00b0"), ("dyn_loft_deg", "Dynamic loft", "\u00b0"),
               ("impact_h_mm", "Impact height", " mm"), ("impact_w_mm", "Impact width", " mm")]
    deep = {"date": latest, "club": dclub, "n": len(drows), "metrics": []}
    for col, label, unit in METRICS:
        lo, avg, hi = agg(vals(drows, col))
        if avg is None:
            continue
        deep["metrics"].append({"label": label, "avg": round(avg, 2), "min": lo, "max": hi, "unit": unit})

    # surfaces, from rounds.json shot-by-shot
    surfaces = {}
    rpath = os.path.join(DATA, "rounds.json")
    if os.path.exists(rpath):
        with open(rpath) as f:
            for rd in json.load(f).get("rounds", []):
                counts = defaultdict(int)
                for h in rd.get("shot_by_shot", []):
                    for sh in h.get("shots", []):
                        counts[sh.get("played_from", "unrecorded")] += 1
                if counts:
                    surfaces[rd["session_id"]] = dict(counts)

    sessions, rounds = [], []
    spath = os.path.join(DATA, "sessions.csv")
    if os.path.exists(spath):
        with open(spath, newline="") as f:
            sessions = list(csv.DictReader(f))
    if os.path.exists(rpath):
        with open(rpath) as f:
            rounds = json.load(f).get("rounds", [])

    logged = {r["session_date"] for r in shots}
    return {"generated": datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC"),
            "face_rows": face_rows, "trend": trend, "bag": bag, "bag_date": bag_date,
            "deep": deep, "surfaces": surfaces, "sessions": sessions, "rounds": rounds,
            "sessions_without_shot_rows": sorted(
                {s["session_date"] for s in sessions if s["session_date"] not in logged})}


if __name__ == "__main__":
    main()
