# Fault Diagnosis Guide (Beginner-Focused)

Use this alongside `protee-vx-metrics.md`. Always reason from the stat pattern shown in the photo — don't assume every top/thin shot has the same cause.

## Face Control at Speed (Steven's current primary fault)

**Signature in the data:** swing path near neutral (within ~1-2°) while **face angle sits
several degrees open**, so face-to-path is large and positive. Right miss scales with club
speed — small or absent in wedges, growing through the mid irons, worst with driver and
fairway woods. Side spin strongly positive, spin axis tilted right. **Closure rate is the
tell**: good swings sit above ~2,200°/s, faulty ones drop toward 1,500-1,900°/s.

**This is a release problem, not a path problem.** The swing shape is fine; the face
simply isn't rotating back to square in time, and faster clubs give it less time.

**Contributing causes, in rough order:**

1. **Holding the face off / steering** — hands don't trust the motion, so they guide
   instead of releasing. Dynamic loft climbs (adding height and spin instead of distance)
   and club speed drops slightly. Very common right after a grip change.
   - Drill: 9-to-3 toe-up at 60-70%. Toe points at the sky at hip height on **both** sides.
   - Feel cue: thumbs point up, club on its edge, "like balancing a cup on the leading edge."
2. **Weak lead-hand grip** — fewer than ~2 knuckles visible at address.
   - Fix: 2-2.5 knuckles. Expect a 2+ week transition dip before power returns.
3. **Weak trail hand** — V pointing at the chin rather than the trail shoulder, palm too
   much on top. Holds the face open through impact and fights a strengthened lead hand.
4. **Grip in the middle of the palm** — restricts forearm rotation mechanically. Note the
   heel pad *should* sit on top; the fault is the shaft across the lifeline.
   - Test: lift lead thumb and index off the club. Secure in the last three fingers = fine.
5. **Equipment contribution** — toe-down dynamic lie adds right bias independently of the
   swing. Hand to `golf-club-fitting`; don't chase it with drills.

**Reading a grip-change session:** expect a *dip*. Compare shots before and after the
change chronologically. Look for proof-of-concept shots on both sides — a well-released
shot with the old grip and a square-faced one with the new grip together show the grip
works and the release is what went missing.

**Sim targets to prescribe:** face 0-3° open, side spin < 500 rpm, closure > 2,200°/s.
Tell him to ignore carry distance entirely while grooving it.

**Pace matters.** Rapid-fire practice (16 shots in 6 minutes) compounds tension and
degrades late-session strikes. One ball per 45-60 seconds, regripping fresh each time.

## Topped / Thinned Shots (historically Steven's recurring miss; now largely resolved on full iron swings)

**Signature in the data:** Impact Point (Vertical) reads low-on-face or "low," dynamic loft much lower than the club's stated loft, ball flight is low and short of expected carry, sometimes a low line-drive "screamer" with almost no apex.

**Most common causes, in rough order of likelihood for a beginner:**

1. **Early extension** — hips/pelvis thrust toward the ball on the downswing, standing the body up and raising the swing's low point above the ball. By far the most common cause.
   - Drill: "wall drill" — set up with hips/butt lightly touching a wall or headcover behind hips; take slow-motion swings keeping contact through impact.
   - Drill: alignment stick in the ground just outside trail hip, feel the hip stay close to it through downswing.
2. **Losing posture / standing up through impact** — often an attempt to "help" the ball up.
   - Drill: swing to a full finish while keeping spine angle from address until well after impact — video/mirror check.
3. **Weight hangs on the back foot** — low point never reaches the ball because weight didn't transfer forward.
   - Drill: step-through drill — take a step toward the target with the trail foot right after impact, forces forward weight shift.
   - Drill: exaggerate finish with 90%+ weight on lead foot, hold for 2 seconds.
4. **Ball position too far forward** — ball sits past the swing's natural low point.
   - Fix: for irons, check ball position is roughly center to slightly forward-of-center in stance, not off the lead heel.
5. **Reverse spine angle** (leaning away from target at the top) — forces a steep-to-shallow-then-up strike pattern.
   - Drill: at the top of the backswing, check in mirror/video that spine tilts slightly *away* from target (normal) without the head/upper body sliding laterally toward the target.

**How to use the data to pick between these:** If Attack Angle is unusually positive for an iron shot (steeper than normal ascending angle) alongside a low impact point, early extension or standing up is most likely. If ball speed/smash factor is very low and weight distribution complaints are mentioned, suspect back-foot weight hang. Ask Steven what it *felt* like (rising up, losing balance, etc.) since VX doesn't measure body motion directly — sim data plus felt sensation together give the real diagnosis.

## Other Common Beginner Misses (for reference)

- **Fat/chunked shots**: low point too far behind ball. Often the opposite compensation from someone who fixed a slice by "staying behind it" too much, or a big weight shift issue in the other direction.
- **Slice** (big left-to-right curve, RH golfer): face-to-path very open (face right of path), often out-to-in swing path.
- **Push/Pull**: face and path aligned to each other but both pointed off target — usually an alignment/setup issue rather than a swing-shape issue.

## General Beginner Coaching Principles
- Prioritize **one fault at a time** — beginners overload easily. Pick the highest-likelihood cause from the data + feel, give 1-2 drills, and check in on it next session before adding something new.
- Always tie a stat back to a feeling or checkpoint the player can self-monitor without a launch monitor (posture, weight, finish position), since most practice won't happen with data in front of them.
- Keep tone encouraging — these are common and fixable patterns.
