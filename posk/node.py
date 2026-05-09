"""
posk/node.py
============
MODULE 4 — Node
Simulates a miner node in the PoSk network.

Each node:
  - Holds a persistent reputation counter (survives across all rounds)
  - Solves challenges independently using type-specific solvers
  - Participates in commit-reveal: commits before seeing peers, reveals after
  - Tracks per-round and cumulative history for benchmarking

Phase 3 additions vs Phase 2:
  - solve() dispatches to three distinct solvers (mathematical/sorting/pattern)
  - commit() and reveal() implement the commit-reveal protocol
  - cheat flag demonstrates tamper detection
  - history list enables benchmarker to compute per-node statistics
"""

import time
import random
from posk.commit_reveal import commit as make_commit, generate_salt


class Node:
    """
    A simulated PoSk miner node.

    Parameters:
      node_id     : str   — unique identifier (e.g. "N1")
      skill_level : float — 0.5 to 1.0, controls solve speed and error rate
      cheat       : bool  — if True, node swaps answer after committing
                            (triggers tamper detection in verification)
    """

    def __init__(self, node_id, skill_level=1.0, cheat=False):
        self.node_id     = node_id
        self.skill_level = skill_level
        self.cheat       = cheat

        # Persistent across all rounds — never reset between rounds
        self.reputation  = 0

        # Cumulative stats for final report / benchmarker
        self.wins        = 0
        self.history     = []   # list of per-round result dicts

        # Per-round state — reset at the start of each solve()
        self._answer     = None
        self._salt       = None
        self._commitment = None
        self._solve_time = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # SOLVING
    # ─────────────────────────────────────────────────────────────────────────

    def solve(self, challenge):
        """
        Attempt the challenge and record the answer + solve time.

        Dispatches to the appropriate solver based on challenge["type"].
        skill_level controls:
          - How quickly the node solves (delay inversely proportional)
          - Probability of making an error (~(1 - skill_level) * 0.35)

        Returns (answer, solve_time_seconds).
        The answer is stored privately for the commit phase.
        """
        # Per-round delay factor: slower nodes take longer
        base_delay = (1.0 / self.skill_level) * 0.003

        ctype = challenge["type"]
        start = time.time()

        if ctype == "mathematical":
            answer = self._solve_collatz(challenge, base_delay)
        elif ctype == "sorting":
            answer = self._solve_sorting(challenge, base_delay)
        elif ctype == "pattern":
            answer = self._solve_pattern(challenge, base_delay)
        else:
            answer = None

        self._solve_time = time.time() - start

        # Simulate errors for lower-skill nodes
        error_prob = (1.0 - self.skill_level) * 0.35
        if random.random() < error_prob and answer is not None:
            # Introduce a small integer error on the answer
            if isinstance(answer, int):
                answer = answer + random.choice([-2, -1, 1, 2])

        self._answer = answer
        return answer, self._solve_time

    def _solve_collatz(self, challenge, delay):
        """
        Iteratively compute Collatz steps from the given start value.
        The step-by-step loop models real compute work.
        """
        n     = challenge["problem"]["start"]
        steps = 0
        while n != 1:
            # Small stochastic delay per iteration to model compute variance
            time.sleep(delay * random.uniform(0.7, 1.3))
            n = n // 2 if n % 2 == 0 else 3 * n + 1
            steps += 1
        return steps

    def _solve_sorting(self, challenge, delay):
        """
        Linear scan for the first out-of-order index.
        Delay scales with list length to model scan time.
        """
        seq = challenge["problem"]["sequence"]
        # One delay unit per element scanned
        time.sleep(delay * len(seq) * random.uniform(0.7, 1.3))
        for i in range(1, len(seq)):
            if seq[i] < seq[i - 1]:
                return i
        return -1

    def _solve_pattern(self, challenge, delay):
        """
        Detect arithmetic or geometric rule, then extrapolate next term.
        Delay scales with sequence length.
        """
        seq = challenge["problem"]["sequence"]
        time.sleep(delay * len(seq) * random.uniform(0.7, 1.3))

        if len(seq) < 2:
            return None

        # Try arithmetic: all consecutive differences equal?
        diffs = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
        if len(set(diffs)) == 1:
            return seq[-1] + diffs[0]

        # Try geometric: all consecutive ratios equal?
        if all(seq[i] != 0 for i in range(len(seq))):
            ratios = [round(seq[i + 1] / seq[i], 6) for i in range(len(seq) - 1)]
            if len(set(ratios)) == 1:
                return int(round(seq[-1] * ratios[0]))

        # Fallback: assume arithmetic using the last difference
        return seq[-1] + diffs[-1]

    # ─────────────────────────────────────────────────────────────────────────
    # COMMIT-REVEAL PROTOCOL
    # ─────────────────────────────────────────────────────────────────────────

    def commit(self):
        """
        COMMIT PHASE — called after solve(), before any reveals.

        Produces:
            commitment = SHA-256( str(answer) + salt )

        The commitment hash is returned (to be broadcast to the network).
        The answer and salt remain private inside this object until reveal().

        If cheat=True: the node commits honestly to its computed answer,
        but will swap to a different answer in reveal() — triggering
        the tamper detection in the consensus manager.
        """
        self._salt, _    = generate_salt(), None   # fresh salt each round
        self._salt       = generate_salt()
        self._commitment, self._salt = make_commit(self._answer)
        return self._commitment

    def reveal(self):
        """
        REVEAL PHASE — called after all commitments are collected.

        Returns (answer, salt) for commitment verification.

        If cheat=True: returns a subtly different answer — the SHA-256
        recomputation in the consensus manager will not match the original
        commitment, and this node is disqualified for the round.
        """
        if self.cheat and isinstance(self._answer, int) and self._answer is not None:
            # Attempt to substitute a 'better' answer after seeing peers commit
            # This will cause a hash mismatch in verify()
            tampered = self._answer - 1
            return tampered, self._salt
        return self._answer, self._salt

    # ─────────────────────────────────────────────────────────────────────────
    # REPUTATION
    # ─────────────────────────────────────────────────────────────────────────

    def update_reputation(self, is_correct):
        """
        Update persistent reputation counter after every round.
        +1 for correct answer, -1 for wrong or tampered (floor = 0).
        """
        if is_correct:
            self.reputation += 1
        else:
            self.reputation = max(0, self.reputation - 1)

    def record_round(self, round_num, challenge_type, is_correct, score):
        """
        Append this round's result to history.
        Called by consensus manager after scoring; used by benchmarker.
        """
        self.history.append({
            "round"      : round_num,
            "type"       : challenge_type,
            "correct"    : is_correct,
            "score"      : score,
            "reputation" : self.reputation,
            "solve_time" : self._solve_time,
        })

    def __repr__(self):
        tag = " [CHEATER]" if self.cheat else ""
        return (f"Node({self.node_id}, skill={self.skill_level}, "
                f"rep={self.reputation}, wins={self.wins}){tag}")