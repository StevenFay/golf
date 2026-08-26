# ProTee VX Stat Glossary

The ProTee VX (via ProTee Labs, and passed through to GSPro) displays up to 24 data points per shot. Steven sends screenshots of the ProTee Labs shot panel (SUMMARY, HISTORY and DATA tabs). Use this glossary to read it correctly.

## Ball Data
- **Ball Speed** (mph/km-h) — speed of the ball right after impact.
- **Total Spin** (rpm) — combined backspin + sidespin.
- **Spin Axis** (degrees, tilt) — tilt of the spin axis; determines curve direction. Positive = fade/slice tendency (right-handed golfer), negative = draw/hook tendency.
- **Back Spin / Side Spin** (rpm) — spin components split out.
- **Launch Direction** (degrees, left/right of target) — initial ball direction relative to target line.
- **Launch Angle** (degrees, vertical) — initial vertical launch of the ball.

## Club Data
- **Club Speed** (mph) — clubhead speed at impact.
- **Swing Path** (degrees, in-to-out or out-to-in) — clubhead's horizontal direction through impact relative to target line.
- **Club Face Angle** (degrees) — where the face points at impact relative to target line.
- **Club Face to Path** — face angle relative to swing path (drives whether it's a draw/fade/hook/slice shape).
- **Attack Angle** (degrees) — vertical direction of the clubhead at impact. Negative = descending strike (normal for irons), positive = ascending strike (normal for driver off a tee).
- **Dynamic Loft** (degrees) — actual loft presented at impact (can differ from the club's stated loft).
- **Club Lie Angle** (degrees) — toe-up/toe-down orientation at impact.
- **Impact Point Vertical / Horizontal** — where on the clubface contact was made (high/low, toe/heel). **This is the single most useful field for diagnosing topped or thinned shots** — a low-face or high-face impact point directly confirms a top/thin miss.

## Flight Data
- **Flight Path, Apex Height, Apex Time**
- **Total Distance / Carry Distance**
- **Air Time / Run**
- **Off Line** (yards/meters left or right of target)
- **Descent Angle**

## Reliability note
Attack Angle and Dynamic Loft readings from the VX are sometimes reported by users as less consistent than Ball Speed, Club Speed, and Impact Point. Weight conclusions accordingly — if Attack Angle/Dynamic Loft conflict with what Impact Point and ball flight are telling you, trust Impact Point and flight result first, and mention the discrepancy rather than silently picking one.

## What a screenshot might NOT show
Not every ProTee Labs layout displays all 24 points — his panel may be a customized subset. If a stat needed for diagnosis isn't visible, say so explicitly and ask for it rather than guessing.

## Which tab shows what
- **SUMMARY** — one shot in detail, including the three impact views (side/front/top),
  impact width/height, dynamic lie, and closure rate. Richest source for a single shot.
- **HISTORY** — the session as a table: carry, offline, speeds, smash, spin axis, spin
  components, launch, face angle, swing path, face-to-path, AoA, dynamic loft. Best source
  for transcribing a whole session.
- **DATA** — per-club aggregates (average, median, std dev, min, max, range). Fastest way
  to get session-level numbers, but hides the chronological story.

Ask for HISTORY when transcribing a session, SUMMARY for a specific interesting shot,
DATA to confirm aggregates.

## Closure Rate (°/s)
Rate of clubface rotation through impact. Not in the original glossary but central to
Steven's current fault. Above ~2,200°/s tends to produce square-to-slightly-closed faces;
below ~1,900°/s the face hangs open. Compare it *within* a session — the absolute number
matters less than the split between his good and bad shots.

## Profile check
The sim carries profiles for both Steven and Amanda. Confirm the name shown on the
screenshot before logging anything.
