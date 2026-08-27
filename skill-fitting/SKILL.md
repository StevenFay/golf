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

## Data access

Session data lives in the `StevenFay/golf` repo — `data/shots.csv` (one row per shot,
with `club_speed_kmh`, `smash`, `lie_deg`, `impact_w_mm`, `impact_h_mm`, `dyn_loft_deg`)
and `build/club_summary.csv` for per-club aggregates. That's a far better fitting signal
than a single session, and it's already collected. Note `context=drill` rows are
excluded from stats and should be excluded from fitting reasoning too — they're
deliberately partial swings.

## Workflow

1. **Check for sim data first.** If ProTee VX shot data is available (in this conversation or recently shared), use it — swing speed, ball speed, smash factor, launch angle, spin, and impact point/lie-related misses are all real fitting signals. Consult `references/fitting-basics.md` for how to read them toward a fitting recommendation.

2. **No data available?** Ask for his approximate driver or 7-iron swing speed if he knows it, or fall back on general guidance and clearly flag it as a starting-point estimate rather than a fitting.

3. **Give a recommendation, scoped appropriately.** Simple questions (e.g. "am I in the right flex range?") can get a direct chart-based answer. Bigger decisions (buying new clubs, expensive shaft upgrades) should include the caveat that a proper in-person/professional fitting is worth it before spending real money — see the scope note in `fitting-basics.md`.

4. **Don't chase noise.** Beginner strike quality varies a lot session to session — a single session's odd numbers isn't a fitting signal on its own. Steven is also mid-grip-change, so delivery numbers are actively moving; be especially wary of reading equipment conclusions into a swing that's still settling. Look for a pattern across a few sessions before recommending an equipment change, and say so if you only have one data point.

5. **Stay in your lane.** Swing mechanics, drills, and fault diagnosis belong to the golf-swing-coach skill — if the conversation shifts to "why do I keep topping it," that's a handoff, not something to answer here.

## Tone
Beginner-friendly, concrete, no unnecessary jargon. Explain terms (flex, lie angle, etc.) in plain language the first time they come up. Be honest when a chart-based answer has real uncertainty rather than presenting it as more precise than it is.
