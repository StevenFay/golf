# Golf practice data

Flatfile backend for simulator practice sessions and SGT rounds.
ProTee VX launch monitor + GSPro.

## Layout

```
data/
  shots.csv       one row per shot, every session, append-only. Source of truth.
  sessions.csv    one row per session: metadata, diagnosis, drills set.
  rounds.json     SGT competitive rounds (nested holes, so JSON suits it).
raw/              original exports and screenshots, never edited.
scripts/
  build.py        regenerates build/ from shots.csv.
  append.py       appends a session CSV into shots.csv with schema checking.
build/            derived output — disposable, regenerate anytime.
```

## The idea

One long table beats a folder of per-session spreadsheets. Any question
("is my 7-iron face angle improving?") becomes one filter over `shots.csv`
instead of opening thirteen files. Git diffs a CSV cleanly, so each new
session shows up as a readable block of added lines, and the file still
opens in Excel if you want to poke at it by hand.

Everything in `build/` is derived. If it disagrees with `shots.csv`,
`shots.csv` wins — delete `build/` and re-run.

## shots.csv schema

| column | notes |
|---|---|
| `session_date` | ISO `YYYY-MM-DD`. Groups shots into sessions. |
| `shot_no` | Shot number as shown by the launch monitor. Gaps are fine. |
| `time` | `HH:MM:SS`, 24h. |
| `club` | `DR 3W 4H 4I 5I 6I 7I 8I 9I PW GW SW LW` |
| `carry_m` `total_m` `offline_m` | Metres. Offline: **positive = right**, negative = left. |
| `club_speed_kmh` `ball_speed_kmh` | km/h. |
| `smash` | Ball speed ÷ club speed. |
| `spin_axis_deg` | Positive = tilted right (fade/slice). |
| `back_spin_rpm` `side_spin_rpm` | Side spin positive = right. |
| `launch_angle_deg` `launch_dir_deg` | Direction positive = right. |
| `face_angle_deg` | Positive = **open**. |
| `swing_path_deg` | Positive = in-to-out. |
| `face_to_path_deg` | Face minus path — the curvature driver. |
| `aoa_deg` | Attack angle. Negative = descending. |
| `dyn_loft_deg` | Dynamic loft at impact. |
| `impact_w_mm` `impact_h_mm` | Strike position on the face. Width positive = toward toe, height positive = above centre. |
| `lie_deg` | Dynamic lie. Positive = toe down. |
| `closure_rate_dps` | Degrees per second of face rotation through impact. |
| `source` | `xlsx_export`, `csv_export` or `screenshot_transcribed`. |

Missing fields are left empty rather than zero-filled — a blank means the
launch monitor didn't report it, which is different from a measured zero.
The `source` column exists because screenshot-transcribed rows carry more
transcription risk than a direct export.

## Adding a session

**From a launch monitor export:**

```bash
python3 scripts/append.py 2026-09-01 /path/to/export.csv
python3 scripts/build.py
```

`append.py` maps common column-name variants onto the schema, refuses to
write if `session_date` already exists (pass `--force` to override), and
prints a summary before committing anything to disk.

**From screenshots:** transcribe into a CSV with whatever columns the
screen showed, then run the same two commands. Set `source` to
`screenshot_transcribed`.

Then add a row to `sessions.csv` with the diagnosis and drills, and commit.

## Reading it

```python
import csv
rows = list(csv.DictReader(open('data/shots.csv')))
seven = [r for r in rows if r['club'] == '7I' and r['face_angle_deg']]
print(sum(float(r['face_angle_deg']) for r in seven) / len(seven))
```

Or `python3 scripts/build.py` and read `build/club_trend.csv`, which has
per-club per-session averages ready to chart.

## Current focus

Face control at speed. Swing path is near-neutral; the clubface doesn't
square by impact, and the miss grows with club speed. Target band is
**face 0–3° open** with **side spin under 500 rpm**.

As of 25 Aug: 4 of 16 seven-irons in the target band.
