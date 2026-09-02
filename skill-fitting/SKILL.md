---
name: golf-club-fitting
description: Provides club fitting guidance (shaft flex, length, lie angle, loft, equipment recommendations) for Steven, a beginner golfer using an indoor sim (ProTee VX + GSPro). Use this skill whenever Steven asks about shaft flex, club length, lie angle, club lofts, whether his current clubs fit him, what clubs/shafts to buy, or generally raises equipment/gear questions — even if he doesn't use the word "fitting." This is a separate skill from golf-swing-coach (which handles swing mechanics, drills, and diagnosis, not equipment) — hand off to that skill for pure swing-fault questions.
---

# Golf Club Fitting — Steven (ProTee VX / GSPro)

Steven is a beginner golfer practicing on an indoor sim (ProTee VX + GSPro) and playing
competitive rounds on Simulator Golf Tour. This skill covers equipment and fitting
questions — shaft flex, length, lie angle, loft, and "should I buy/change X" decisions.
He shares the sim with Amanda; ProTee Labs has profiles for both, so check the profile
name on any screenshot before drawing conclusions from the data.

## Open fitting items

- **Dynamic lie ~7° toe-down** (25 Aug 7-iron block, range 4.0–9.7°). Toe-down delivery
  points shots right independently of the swing, and Steven's primary fault is already a
  right miss — so this needs separating from the swing work rather than being conflated
  with it. Worth a lie-angle check.
- **Iron lofts unknown, and it matters.** On 26 Aug three 7-irons read smash 1.36–1.45
  with dynamic loft 23.8–25.4°. If the set is strong-lofted (28–30° 7-iron), those are
  normal good strikes and every smash benchmark shifts up; if it's a traditional 34°,
  the numbers need another explanation. **Get the stamped lofts** — they recalibrate the
  targets for the whole set.
- **New irons were incoming** as of 22 Aug. Re-map carries and re-check lie when they
  land; the existing gapping data won't transfer.
- **Heel-biased contact.** 29 Aug round: `impact_w_mm` negative on nearly every shot,
  ranging to −30 mm. Combined with toe-down lie, worth checking distance from the ball
  and lie angle together rather than separately.
- **Gapping overlaps at the top of the bag.** From the 22 Aug session: 4I, 4H and 3W all
  carried 170–173 m, and 5I and 6I sat 4 m apart. Three clubs covering one number is a
  set-composition question, not a swing one.

## Worked example — answering a lie-angle question from the repo

1. Pull `build/club_summary.csv`, scope `all_time`, and read `lie_avg` / `lie_min` /
   `lie_max` per club.
2. Cross-check `impact_w_avg`: consistent heel contact with toe-down lie points to the
   club sitting too upright **or** Steven standing too close — those need separating.
3. Check `offline_avg` direction: toe-down delivery pushes shots right, which is also
   his swing miss, so do not attribute the whole bias to the club.
4. Check the coverage line from `scripts/build.py` before concluding. If `lie_deg` is
   thin, say how thin.
5. If the recommendation would cost money, say a proper in-person fitting comes first.

## Data access — GitHub repo `StevenFay/golf`

All of Steven's shot data lives in one repo. This is a far better fitting signal than
whatever happens to be in the current conversation, and it is already collected.

```
data/shots.csv       one row per shot, every session, append-only. Source of truth.
data/sessions.csv    session metadata: description, diagnosis, drills.
data/rounds.json     SGT rounds with per-hole detail and played-from surfaces.
raw/                 original exports and screenshots, never edited.
scripts/build.py     regenerates build/ from shots.csv.
build/club_summary.csv   per-club aggregates: min/avg/max on every metric.
build/club_trend.csv     per-club, per-session averages — for spotting drift.
build/dashboard_data.json  everything the dashboard renders.
```

**Access:** Steven pastes a GitHub token when he wants writes; it does not persist
between conversations. Reads can go through the API with that token. If it isn't in the
current chat, ask for it, or ask him to paste the relevant rows.

### The columns that matter for fitting

| Question | Columns |
|---|---|
| Lie angle | `lie_deg` (dynamic lie, **positive = toe down**), `impact_w_mm` (**negative = heel**), `offline_m` |
| Shaft flex / weight | `club_speed_kmh`, `back_spin_rpm`, `launch_angle_deg`, `dyn_loft_deg` |
| Length | `impact_w_mm` and `impact_h_mm` scatter, `smash` consistency |
| Loft / gapping | `carry_m` by club from `build/club_summary.csv`, `dyn_loft_deg`, `descent_angle_deg`, `apex_m` |
| Strike quality | `smash`, `impact_w_mm`, `impact_h_mm` |

### Rules for reading this data

1. **Exclude what the build excludes.** `context=drill` rows are deliberately partial
   swings. `exclude_from_stats=1` marks punch-outs, knockdowns and recoveries. Club `P`
   is putts. None belong in fitting reasoning — and `build/club_summary.csv` has already
   dropped them, so prefer it over hand-filtering `shots.csv`.
2. **Use `carry_m`, never `carry_game_m`.** `carry_m` is what ProTee measured from the
   strike. `carry_game_m` is what GSPro played after applying a lie penalty — from rough
   that can be 25–38 m shorter. Only `carry_m` reflects the club.
3. **Every shot is off the same flat mat**, including rounds. So delivery and impact
   data is directly comparable across `practice`, `sgt` and `play`; there is no
   "he was in the rough" explanation for a bad lie-angle reading.
4. **Check coverage before concluding.** `scripts/build.py` prints per-column fill
   rates. `lie_deg` in particular is only captured on SUMMARY-panel screenshots — as of
   the last check just 6 of 168 rows have it. A lie recommendation resting on 6 shots
   from one session must say so.
5. **Watch for club mislabels.** The sim has logged an entire 9-iron block as 8-iron
   before, and club assignment on round captures is *inferred* from a club box that runs
   one shot ahead. Sanity-check carry against the club before trusting it.
6. **Check the profile.** ProTee Labs carries profiles for both Steven and Amanda.
   `shots.csv` should be Steven only, but verify on any new screenshot.

### Current data snapshot

Roughly 170 shots across four sessions (22 Aug full-bag gapping, 25 and 26 Aug iron
blocks, 29 Aug SGT round). Re-read `build/club_summary.csv` rather than trusting these
figures — they date quickly.

## Workflow

1. **Check for sim data first.** If ProTee VX shot data is available (in this conversation or recently shared), use it — swing speed, ball speed, smash factor, launch angle, spin, and impact point/lie-related misses are all real fitting signals. Consult `references/fitting-basics.md` for how to read them toward a fitting recommendation.

2. **No data available?** Ask for his approximate driver or 7-iron swing speed if he knows it, or fall back on general guidance and clearly flag it as a starting-point estimate rather than a fitting.

3. **Give a recommendation, scoped appropriately.** Simple questions (e.g. "am I in the right flex range?") can get a direct chart-based answer. Bigger decisions (buying new clubs, expensive shaft upgrades) should include the caveat that a proper in-person/professional fitting is worth it before spending real money — see the scope note in `fitting-basics.md`.

4. **Don't chase noise.** Beginner strike quality varies a lot session to session — a single session's odd numbers isn't a fitting signal on its own. Steven is also mid-grip-change, so delivery numbers are actively moving; be especially wary of reading equipment conclusions into a swing that's still settling. Look for a pattern across a few sessions before recommending an equipment change, and say so if you only have one data point.

5. **Stay in your lane.** Swing mechanics, drills, and fault diagnosis belong to the golf-swing-coach skill — if the conversation shifts to "why do I keep topping it," that's a handoff, not something to answer here.

## Tone
Beginner-friendly, concrete, no unnecessary jargon. Explain terms (flex, lie angle, etc.) in plain language the first time they come up. Be honest when a chart-based answer has real uncertainty rather than presenting it as more precise than it is.
