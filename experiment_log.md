# AI Beam Search — Experiment Log

All benchmarks run on the simulator at difficulty 2 (100 bullets), 100s cap, 8-way parallel, unless noted otherwise.

---

## Baseline

**Config:** `DEPTH=10, WIDTH=8, CHECK_EVERY=4` (40f / 0.5s lookahead)

| Metric | Value |
|--------|-------|
| Avg survival | 53.5s |
| Cap rate | 41% |
| Worst case | 2.2s |

**Scoring:** Inverse-square danger (`2000/d²`), no safety margin, strong center pull (2.0).

---

## Experiment 1: Deeper Lookahead

### 1a. DEPTH=16, WIDTH=12, CHECK_EVERY=4
**Hypothesis:** 2× deeper lookahead + wider beam = more escape routes found.

| Avg | Cap% | Verdict |
|-----|------|---------|
| ~54.1s | — | ❌ No improvement |

**Why:** Beam width alone can't compensate for shallow lookahead. The AI still can't see bullets far enough ahead to plan escapes through dense patterns.

### 1b. DEPTH=40, WIDTH=8, CHECK_EVERY=4 ✅
**Hypothesis:** 4× deeper lookahead (160f / 2.0s) covers full bullet travel time.

| Avg | Cap% | Worst | Verdict |
|-----|------|-------|---------|
| 67.3s | 46% | 6.1s | ✅ +26% over baseline |

**Why it worked:** 2.0s lookahead lets the beam see approaching bullets early enough to route around them. Early deaths (2-5s) eliminated — worst case improved from 2.2s → 6.1s. Also added 2px safety margin and gentler center pull (0.3).

---

## Experiment 2: Beam Width Sweep

All at DEPTH=40, CHECK_EVERY=4.

### 2a. WIDTH=6 (DEPTH=60, CHECK_EVERY=5)
**Hypothesis:** Compensate narrow beam with even deeper lookahead.

| Avg | Verdict |
|-----|---------|
| 60.8s | ❌ Worse than WIDTH=8 |

**Why:** 6 paths isn't enough diversity — beam collapses to local minima. The extra depth (300f) doesn't help if all paths lead to the same dead end.

### 2b. WIDTH=10
**Hypothesis:** More path diversity = more escape routes.

| Avg | Cap% | Verdict |
|-----|------|---------|
| 72.2s | 50% | ✅ +7% over WIDTH=8 |

**Why:** 10 paths provide enough diversity to explore multiple escape directions simultaneously, especially in multi-directional bullet spreads.

### 2c. WIDTH=12 ✅✅ (BEST)
**Hypothesis:** Push wider still.

| Avg | Cap% | Worst | Verdict |
|-----|------|-------|---------|
| 77.6s | 62% | 3.4s | ✅✅ +35% over baseline |

**Why:** 12 paths hits the sweet spot — enough diversity to find escape routes in dense patterns without excessive computation. 62% of runs reach the 100s cap.

### 2d. WIDTH=14
**Hypothesis:** Even wider = even better?

| Avg | Cap% | Verdict |
|-----|------|---------|
| 71.0s | 54% | ❌ Diminishing returns |

**Why:** Beyond ~12 paths, the beam keeps too many mediocre paths that crowd out good ones. Also: the extra paths share similar first moves, wasting diversity.

---

## Experiment 3: Check Granularity

### 3a. CHECK_EVERY=2, DEPTH=40 (80f / 1.0s horizon)
**Hypothesis:** Finer checks catch bullets that slip between 4f gaps.

| Avg | Cap% | Verdict |
|-----|------|---------|
| 59.1s | 46% | ❌ |

**Why:** Halving the check interval also halves the total lookahead horizon (1.0s vs 2.0s). The shorter horizon hurts more than finer checks help. Bullets move ~3px/frame, so 4f gaps (12px) are fine for the 11px hitbox.

### 3b. CHECK_EVERY=2, DEPTH=80 (160f / 2.0s horizon)
**Hypothesis:** Finer checks + same horizon.

| Avg | Cap% | Verdict |
|-----|------|---------|
| 60.6s | 46% | ❌ |

**Why:** Finer granularity makes the beam overreact to near-term micro-threats, losing sight of the macro escape path. The coarser 4f step acts as a natural smoothing filter.

---

## Experiment 4: Directional Danger Scoring

**Hypothesis:** Bullets moving toward the player are more dangerous than those moving away. Model this with approach vector dot product.

### 4a. Aggressive directional (approach bonus + 0.25× retreat weight)
| Avg | Cap% | Worst | Verdict |
|-----|------|-------|---------|
| 73.7s | 56% | 2.9s | ⚠️ Mixed |

**Why it helped avg:** Correctly identifies approaching threats sooner.
**Why it hurt worst-case:** Homing bullets (Type 1) retreat then re-aim toward the player. Discounting retreating bullets to 0.25× caused the AI to confidently walk into paths that later become deadly.

### 4b. Conservative directional (approach bonus + 0.6× retreat weight)
| Avg | Cap% | Verdict |
|-----|------|---------|
| 69.8s | 48% | ❌ |

### 4c. Additive approach bonus (no retreat discount)
| Avg | Cap% | Verdict |
|-----|------|---------|
| 65.8s | 42% | ❌ Worse than baseline |

**Conclusion:** Directional scoring adds noise without net benefit. The base inverse-square danger already captures what matters — *where* bullets are is more important than *which direction* they're moving, because homing bullets can change direction.

---

## Experiment 5: Gap Bonus Scoring

**Hypothesis:** Reward positions far from the nearest bullet (explicit gap detection).

| Avg | Cap% | Worst | Verdict |
|-----|------|-------|---------|
| 59.7s | 40% | 2.8s | ❌ Regressed |

**Why:** The gap bonus (subtracting `500/(closest_dist+10)` from danger) created a non-monotonic scoring function where positions near one bullet but far from others scored similarly to positions moderately far from all bullets. This confused the beam search's top-K selection.

---

## Final Optimal Config

```
BEAM_DEPTH = 40      # 160f / 2.0s lookahead
BEAM_WIDTH = 12      # 12-path beam diversity
CHECK_EVERY = 4      # evaluate every 4th frame
```

**Scoring:**
- Inverse-square danger: `2000 / d²` per bullet
- Safety margin: 2px buffer around 11×10 hitbox
- Center pull: 0.3 weight (gentle — avoids overriding danger)
- Wall penalty: 5000 within 10px of edges
- Time decay: `w = 1/(0.5 + t × 0.03)` — near-term threats weighted higher

**Final results (100 runs each):**

| Difficulty | Bullets | Avg | Cap% | Worst | vs Human |
|-----------|---------|-----|------|-------|----------|
| Diff 1 | 50 | 79.7s | 60% | 10.7s | 3.8× (21.1s) |
| Diff 2 | 100 | 72.2s | 59% | 2.5s | — |

---

## Key Takeaways

1. **Lookahead depth is the most impactful parameter.** Going from 10→40 steps (+26%) was the single biggest gain. The beam must see far enough to route around bullet clusters.

2. **Beam width has a sweet spot.** Too narrow (6) collapses to local minima. Too wide (14) keeps noise. 10-12 paths is optimal for this bullet density.

3. **Coarser check intervals are better.** CHECK_EVERY=4 acts as implicit smoothing — the beam focuses on macro escape routes rather than overreacting to frame-by-frame micro-threats.

4. **Directional/velocity-based scoring does not help.** Bullets change direction (homing, bouncing), so velocity is unreliable. Position-based inverse-square danger is simpler and more robust.

5. **Simple scoring beats complex.** The winning config uses the simplest scoring function tested. Gap bonuses, approach vectors, and directional weighting all added noise that confused the beam's top-K selection.

6. **Safety margin matters.** 2px buffer around the hitbox prevents the AI from threading gaps that are physically impassable at 1px/frame movement.
