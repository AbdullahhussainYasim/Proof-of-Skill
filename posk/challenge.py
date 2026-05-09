"""
posk/challenge.py
=================
MODULE 2 — Challenge Generator
Produces verifiable computational tasks for each consensus round.

Phase 3: three distinct challenge types, all difficulty-parameterised.
  1. mathematical  — Collatz sequence step count
  2. sorting       — find first out-of-order index in a sequence
  3. pattern       — predict next term in arithmetic/geometric series

Each challenge dict contains:
  type           : str   – challenge category
  tier           : int   – difficulty 1–5
  description    : str   – human-readable task summary
  problem        : dict  – the actual input data shown to nodes
  correct_answer : any   – known only to generator + evaluator
                           nodes must compute this themselves
"""

import random

# All available challenge types — randomly selected each round
CHALLENGE_TYPES = ["mathematical", "sorting", "pattern"]


def generate_challenge(difficulty_tier, force_type=None):
    """
    Entry point for the Consensus Manager.

    difficulty_tier : int 1–5, controls problem size and complexity
    force_type      : optionally pin a specific type (used in testing)

    Returns a challenge dict with 'correct_answer' embedded.
    The correct_answer is NEVER sent to nodes — they must derive it.
    """
    ctype = force_type if force_type else random.choice(CHALLENGE_TYPES)

    generators = {
        "mathematical" : _collatz_challenge,
        "sorting"      : _sorting_challenge,
        "pattern"      : _pattern_challenge,
    }

    if ctype not in generators:
        raise ValueError(f"Unknown challenge type: '{ctype}'")

    return generators[ctype](difficulty_tier)


# ─────────────────────────────────────────────────────────────────────────────
# CHALLENGE TYPE 1: MATHEMATICAL — Collatz Sequence
# ─────────────────────────────────────────────────────────────────────────────

def _collatz_challenge(tier):
    """
    COLLATZ SEQUENCE STEP COUNT
    ───────────────────────────
    Given a starting integer n > 1, count how many steps the Collatz
    sequence takes to reach 1, following the rules:
      - If n is even  →  n = n / 2
      - If n is odd   →  n = 3n + 1
      - Stop when n == 1; the step count is the answer.

    This is a genuine mathematical problem with no shortcut formula —
    nodes must iterate to solve it. Higher tiers use larger starting
    numbers, which produce longer sequences.

    Complexity: O(steps) where steps grows roughly logarithmically
    with the starting number but is unpredictable (open Collatz conjecture).

    Tier mapping:
      Tier 1: start in [50,  200]   ~short sequences
      Tier 2: start in [200, 500]
      Tier 3: start in [500, 1000]
      Tier 4: start in [1000,3000]
      Tier 5: start in [3000,8000]  ~long sequences
    """
    ranges = {1: (50, 200), 2: (200, 500), 3: (500, 1000),
              4: (1000, 3000), 5: (3000, 8000)}
    lo, hi = ranges.get(tier, (50, 200))
    start  = random.randint(lo, hi)

    # Pre-compute the correct answer for later verification
    n, steps = start, 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1

    return {
        "type"           : "mathematical",
        "tier"           : tier,
        "description"    : "Collatz sequence — count steps from start to 1",
        "problem"        : {"start": start},
        "correct_answer" : steps,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CHALLENGE TYPE 2: SORTING — First Out-of-Order Index
# ─────────────────────────────────────────────────────────────────────────────

def _sorting_challenge(tier):
    """
    FIRST OUT-OF-ORDER INDEX
    ────────────────────────
    Given a list of integers, find the index (0-based) of the FIRST element
    that is strictly less than its predecessor. If the list is already fully
    sorted in non-descending order, the answer is -1.

    Nodes must scan left-to-right and return the first violation index.
    Higher tiers use longer lists with larger value ranges, increasing
    the scan cost and making position harder to guess.

    Tier mapping:
      Tier 1: 20  elements, values 1–100
      Tier 2: 35  elements, values 1–300
      Tier 3: 55  elements, values 1–600
      Tier 4: 80  elements, values 1–1000
      Tier 5: 120 elements, values 1–2000
    """
    lengths = {1: 20, 2: 35, 3: 55, 4: 80, 5: 120}
    ranges  = {1: 100, 2: 300, 3: 600, 4: 1000, 5: 2000}

    length   = lengths.get(tier, 20)
    max_val  = ranges.get(tier, 100)
    sequence = [random.randint(1, max_val) for _ in range(length)]

    # 65% chance we deliberately inject an out-of-order element
    correct_answer = -1
    if random.random() < 0.65:
        # Pick a non-boundary index and make it clearly smaller than predecessor
        idx             = random.randint(1, length - 2)
        sequence[idx]   = sequence[idx - 1] - random.randint(1, max(1, max_val // 10))
        # Find the FIRST violation (may be earlier than idx if random generated one)
        for i in range(1, len(sequence)):
            if sequence[i] < sequence[i - 1]:
                correct_answer = i
                break

    return {
        "type"           : "sorting",
        "tier"           : tier,
        "description"    : "Find first out-of-order index (-1 if fully sorted)",
        "problem"        : {"sequence": sequence},
        "correct_answer" : correct_answer,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CHALLENGE TYPE 3: PATTERN — Predict Next Term
# ─────────────────────────────────────────────────────────────────────────────

def _pattern_challenge(tier):
    """
    SEQUENCE PATTERN RECOGNITION
    ─────────────────────────────
    Given the first N terms of a numeric sequence, predict the next term.

    The sequence is either:
      Arithmetic  : each term increases by a fixed step
                    e.g. [3, 7, 11, 15] → step=4 → next=19
      Geometric   : each term multiplies by a fixed ratio (at tier >= 3)
                    e.g. [2, 6, 18, 54] → ratio=3 → next=162

    Difficulty affects:
      - Number of terms shown (fewer clues at higher tiers)
      - Step/ratio magnitude (larger = harder to spot)
      - Whether geometric sequences appear (only at tier 3+)

    Tier mapping:
      Tier 1: 7 terms shown, arithmetic only,  step 2–10
      Tier 2: 6 terms shown, arithmetic only,  step 5–25
      Tier 3: 5 terms shown, arith or geo,     step 8–40  / ratio 2–3
      Tier 4: 4 terms shown, arith or geo,     step 15–70 / ratio 2–5
      Tier 5: 3 terms shown, arith or geo,     step 20–100/ ratio 2–7
    """
    clues      = {1: 7, 2: 6, 3: 5, 4: 4, 5: 3}
    step_range = {1: (2,10), 2: (5,25), 3: (8,40), 4: (15,70), 5: (20,100)}
    ratio_range= {3: (2,3), 4: (2,5), 5: (2,7)}

    n_clues    = clues.get(tier, 5)
    use_geo    = tier >= 3 and random.random() < 0.45

    if use_geo:
        lo, hi  = ratio_range[tier]
        ratio   = random.randint(lo, hi)
        start   = random.randint(1, 10)
        terms   = [start * (ratio ** i) for i in range(n_clues + 1)]
    else:
        lo, hi  = step_range[tier]
        step    = random.randint(lo, hi)
        start   = random.randint(1, 50)
        terms   = [start + step * i for i in range(n_clues + 1)]

    return {
        "type"           : "pattern",
        "tier"           : tier,
        "description"    : "Predict the next term in the sequence",
        "problem"        : {"sequence": terms[:n_clues]},   # hide the answer
        "correct_answer" : terms[n_clues],                  # this is the answer
    }