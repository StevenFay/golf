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

## Contexts

**Everything here is simulator data** — ProTee VX + GSPro. There is no outdoor
data and no plan for any, so the distinction that matters is what kind of
session a shot came from:

| context | what it is | in stats? |
|---|---|---|
| `practice` | Training and block work on the range | yes |
| `sgt` | Simulator Golf Tour competitive rounds | yes |
| `play` | General casual rounds | yes |
| `drill` | Drill reps — 9-to-3, half speed, shortened swings | **no** |

**Individual shots can also be excluded.** Some swings were never meant to be full
ones — a punch-out from behind a tree, a deliberate knockdown, a stymied recovery.
They are real golf and belong in the round, but pooling them into club averages
misrepresents what the club does. Set `exclude_from_stats=1` with a reason;
`build.py` lists every excluded shot on each run, so it never happens silently.

Drills are excluded from every average because they are *deliberately* partial
swings. A 60% 9-to-3 rep carrying 60 m is a successful drill, but pooled into a
gapping table it would quietly drag the 8-iron average down and widen the band.
They're still logged, and still summarised under their own `context_drill` scope,
so drill progress can be tracked without contaminating anything else.

**Every shot is struck off the same flat mat**, including SGT and casual rounds.
The virtual courses have genuine rough, sand and water, and finding them costs
strokes. GSPro applies **distance and spin penalties** to shots played from rough,
deep rough and sand — it takes the measured ball data and degrades the flight it
simulates.

The line that matters for this dataset:

| | affected by lie? |
|---|---|
| Delivery: club speed, face angle, swing path, smash, impact position, AoA | **no** — always off the mat, directly comparable across all contexts |
| Ball at launch: ball speed, spin, launch angle (as measured by ProTee) | **no** — measured before the game touches it |
| Carry / total **as played in GSPro** | **yes** — distance and spin penalties applied |

So for a shot from rough, ProTee Labs and GSPro report different carries for the
same swing. `shots.csv` holds the ProTee figure — the clean physical result of the
strike. That will not match what the course showed, and that is correct. If the
as-played distance ever matters, it belongs in `rounds.json` alongside the hole
result, not in `shots.csv`.

Note also that `shots.csv`
What genuinely does differ on-course is **shot intent and pressure**: deliberate
partial wedges, knockdowns and awkward yardages dilute a carry average, and
tournament nerves are real. That's a reason to keep the `context_*` scopes, not a
reason to split the headline number.

`build/club_summary.csv` carries an `all_time` scope (everything except drills),
the latest session, and a `context_*` scope per context, so practice and
on-course numbers sit side by side while the headline figure stays whole.

## Descriptions

Every session carries a human `description` in `sessions.csv` (or `rounds.json`
for rounds), separate from `context`. Context says *what kind*; description says
*which one*:

- `SGT Tour Championship Round 1 front nine`
- `Keperra West Course casual with Amanda`
- `7-iron block, first trial of the stronger grip`

`append.py` refuses an import without `--description`, and `build.py` warns about
any `session_id` in `shots.csv` that has no description recorded. A session
labelled only `2026-08-26-practice` is unidentifiable a month later.

## Surfaces

`surface` records what the ball was sitting on. Source it from the **SGT shot-by-shot
cards**, which state it outright (`231 YDS TO FAIRWAY`, `175 YDS TO DEEPROUGH`) and
join to shots by hole and shot number. The GSPro screen shows the lie only as a grass
texture, so don't infer it from a screenshot.

The critical distinction:

- **Delivery data is comparable across all surfaces.** The strike is always off the
  same flat mat, so club speed, face angle, path, smash and impact position mean the
  same thing whether the ball was "in" rough or on a tee.
- **`carry_game_m` is NOT comparable across surfaces**, because that's precisely where
  GSPro's penalty lands. Compare it only within the same surface.
- The **gap between `carry_m` and `carry_game_m`** is the penalty itself — useful for
  learning what a given lie actually costs, which is real club-selection information.

What genuinely differs by surface is *intent*: a swing from deep rough is often a
deliberate hack-out, which is what `shot_type` and `exclude_from_stats` are for.

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
| `session_date` | ISO `YYYY-MM-DD`. |
| `session_id` | `{date}-{context}`, plus an optional suffix (`2026-09-01-sgt-r2`). The real session key — **a date is not unique**, since a warm-up block and an SGT round can share a day. Joins to `sessions.csv` / `rounds.json`, where the human `description` lives. |
| `shot_no` | Shot number as shown by the launch monitor. Gaps are fine. |
| `time` | `HH:MM:SS`, 24h. |
| `club` | `DR 3W 4H 4I 5I 6I 7I 8I 9I PW GW SW LW` |
| `context` | One of `practice`, `sgt`, `play`, `drill`. See below. |
| `surface` | What the ball was sitting on in GSPro: `tee`, `fairway`, `rough`, `deep_rough`, `sand`, `green`, `recovery`. On-course only. |
| `shot_type` | `full` (default), or `punch`, `knockdown`, `recovery`, `partial`. Descriptive. |
| `exclude_from_stats` | `1` to drop this single shot from every average. |
| `exclude_reason` | Why — required in practice, since `build.py` prints it on every run. |
| `hole` | Hole number, for `sgt` and `play` only. Joins to the matching date's round in `rounds.json`. Blank otherwise. |
| `carry_m` | Metres, **as measured by ProTee** from the ball's launch conditions. No lie penalty. This is the swing's true output. |
| `carry_game_m` | Metres, **as played in GSPro** — after its distance and spin penalty. Shown on the capture as "CARRY (game)" beside "CARRY (raw)". |
| `total_m` `offline_m` | Metres. Offline: **positive = right**, negative = left. |
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

**From a launch monitor export (practice):**

```bash
python3 scripts/append.py 2026-09-01 /path/to/export.csv
python3 scripts/build.py
```

**From a played round (SGT or casual):**

```bash
python3 scripts/append.py 2026-09-01 round.csv --context sgt --hole 7
python3 scripts/append.py 2026-09-01 round.csv --context play --hole 3
# or include a 'hole' column in the CSV and omit --hole
```

On-course imports must carry a hole number — `append.py` refuses without one,
and `build.py` warns if a hole doesn't exist in that date's round in
`rounds.json`, so the join can't silently drop shots.

**Drill reps:**

```bash
python3 scripts/append.py 2026-09-01 drills.csv --context drill
```

No hole needed. Logged, summarised separately, excluded from all averages.

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
per-club per-session averages with `context` as a column, so charts can split
by session type rather than averaging everything together.

## Current focus

Face control at speed. Swing path is near-neutral; the clubface doesn't
square by impact, and the miss grows with club speed. Target band is
**face 0–3° open** with **side spin under 500 rpm**.

As of 25 Aug: 4 of 16 seven-irons in the target band.
