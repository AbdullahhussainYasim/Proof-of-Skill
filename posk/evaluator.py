"""
posk/evaluator.py
=================
MODULE 5 — Skill Evaluator
Computes the four-component PoSk skill score for each node per round.

Formula (unchanged from Phase 2 v2):
    PoSk_Score(n) = w1·A(n) + w2·E(n) + w3·D + w4·R(n)
    = 0.35·A + 0.30·E + 0.20·D + 0.15·R

Components:
  A(n) — Accuracy   : 1.0 correct | 0.0 wrong/tampered/timeout
  E(n) — Efficiency : normalised inverse solve time (faster = higher)
  D    — Difficulty : raw tier value 1–5 (same for all nodes per round)
  R(n) — Reputation : normalised historical reputation (higher rep = higher R)

All components except D are normalised to [0.0, 1.0] within each round.
D is deliberately kept un-normalised as a multiplier to reward harder rounds.
"""

# ── Weights — must sum to 1.0 ──────────────────────────────────────────────
W1 = 0.35   # Accuracy   — correctness is the primary criterion
W2 = 0.30   # Efficiency — speed rewards genuine capability
W3 = 0.20   # Difficulty — harder rounds deserve amplified reward
W4 = 0.15   # Reputation — history matters but doesn't dominate


def accuracy_score(is_correct):
    """
    A(n): Binary accuracy component.
      1.0 — correct answer (verified via commit-reveal)
      0.0 — wrong answer, timeout, or tampered commitment

    Note: Phase 2 included a 0.5 partial credit option.
    Phase 3 removes partial credit because commit-reveal produces
    a definitive binary verdict (honest+correct or disqualified).
    """
    return 1.0 if is_correct else 0.0


def efficiency_score(t_n, t_min, t_max):
    """
    E(n): Normalised efficiency (solve speed) component.

        E(n) = 1 - (t_n - t_min) / (t_max - t_min)

    The fastest node gets E=1.0, the slowest gets E=0.0.
    All other nodes are linearly interpolated between them.

    Guard condition:
        if t_max == t_min (all nodes solved in identical time)
        → E(n) = 1.0 for all nodes (no penalty for ties)
        This prevents division by zero.

    Only correct nodes contribute to the t_min/t_max range —
    disqualified or wrong nodes use all-node times as fallback.
    """
    if t_max == t_min:
        return 1.0
    e = 1.0 - (t_n - t_min) / (t_max - t_min)
    # Clamp to [0, 1] — floating point arithmetic can give tiny negatives
    return max(0.0, min(1.0, e))


def reputation_score(rep_n, rep_min, rep_max):
    """
    R(n): Normalised historical reputation component.

        R(n) = (rep_n - rep_min) / (rep_max - rep_min)

    The node with the highest raw reputation gets R=1.0,
    the lowest gets R=0.0. Linear interpolation between them.

    Guard condition:
        if rep_max == rep_min (all nodes have identical reputation,
        including the all-zero case in Round 1)
        → R(n) = 1.0 for all nodes (reputation is neutral, not punishing)
        This ensures new nodes aren't disadvantaged purely because
        of the normalisation formula in early rounds.
    """
    if rep_max == rep_min:
        return 1.0
    return (rep_n - rep_min) / (rep_max - rep_min)


def compute_skill_score(a, e, d, r):
    """
    Full PoSk skill score computation.

        PoSk_Score = w1·A + w2·E + w3·D + w4·R
                   = 0.35·A + 0.30·E + 0.20·D + 0.15·R

    Returns a float. The range is approximately:
      Min: 0.0  (wrong, slowest, tier 1, lowest rep)
      Max: ~2.0 (correct, fastest, tier 5, highest rep)
        = 0.35 + 0.30 + 0.20×5 + 0.15 = 1.80
    """
    return W1 * a + W2 * e + W3 * d + W4 * r


def score_all_nodes(node_results, difficulty_tier):
    """
    Convenience function: score every node in node_results dict.

    node_results : { node_id: { "is_correct", "solve_time", "rep_before", ... } }
    difficulty_tier : int 1–5

    Mutates each result dict in-place, adding keys:
        "A", "E", "R", "score"

    Returns the same dict for chaining.
    """
    # Compute normalisation ranges using ONLY correct (honest) nodes for E
    correct = [r for r in node_results.values() if r["is_correct"]]
    times   = ([r["solve_time"] for r in correct]
               if correct else [r["solve_time"] for r in node_results.values()])
    t_min, t_max = min(times), max(times)

    reps    = [r["rep_before"] for r in node_results.values()]
    rep_min, rep_max = min(reps), max(reps)

    for r in node_results.values():
        a = accuracy_score(r["is_correct"])
        e = efficiency_score(r["solve_time"], t_min, t_max)
        d = difficulty_tier
        rv = reputation_score(r["rep_before"], rep_min, rep_max)
        r["A"]     = a
        r["E"]     = e
        r["R"]     = rv
        r["D"]     = d
        r["score"] = compute_skill_score(a, e, d, rv)

    return node_results