"""
Proof of Skill (PoSk) - Phase 2 Prototype v2
=============================================
Changes from v1:
  - Added Historical Reputation Score R(n) as a 4th component
  - Updated weights: w1=0.35, w2=0.30, w3=0.20, w4=0.15
  - Reputation is a global counter per node: +1 correct, -1 wrong, floor=0
  - R(n) is normalised 0.0-1.0 using same logic as E(n)
  - Guard: if all reputations equal, R(n)=1.0 for all nodes

Updated Formula:
  PoSk_Score(n) = w1*A(n) + w2*E(n) + w3*D(n) + w4*R(n)

Phase 3 will extend this with:
  - Multiple rounds / full simulation loop
  - Dynamic challenge generation (3+ task types)
  - Commit-reveal scheme to prevent solution copying
  - Performance benchmarking and graphs
"""

import hashlib
import time
import random


# ─────────────────────────────────────────
# MODULE 1: Blockchain
# ─────────────────────────────────────────

class Block:
    """Represents a single block in the PoSk chain."""

    def __init__(self, index, previous_hash, proposer, skill_score,
                 transactions, reputation_snapshot):
        self.index               = index
        self.timestamp           = time.time()
        self.previous_hash       = previous_hash
        self.proposer            = proposer
        self.skill_score         = round(skill_score, 4)
        self.transactions        = transactions
        self.reputation_snapshot = reputation_snapshot   # dict: {node_id: rep}
        self.hash                = self.compute_hash()

    def compute_hash(self):
        block_data = (
            f"{self.index}"
            f"{self.timestamp}"
            f"{self.previous_hash}"
            f"{self.proposer}"
            f"{self.skill_score}"
            f"{self.transactions}"
            f"{self.reputation_snapshot}"
        )
        return hashlib.sha256(block_data.encode()).hexdigest()

    def __repr__(self):
        rep_str = ", ".join(f"{k}={v}" for k, v in self.reputation_snapshot.items())
        return (
            f"\n  Block #{self.index}"
            f"\n    Proposer          : {self.proposer}"
            f"\n    Skill Score       : {self.skill_score}"
            f"\n    Transactions      : {self.transactions}"
            f"\n    Reputation Snap   : {{{rep_str}}}"
            f"\n    Hash              : {self.hash[:24]}..."
            f"\n    Prev Hash         : {self.previous_hash[:24]}..."
        )


class Blockchain:
    """Manages the chain of PoSk blocks."""

    def __init__(self):
        self.chain = [self._create_genesis_block()]

    def _create_genesis_block(self):
        return Block(
            index=0,
            previous_hash="0" * 64,
            proposer="GENESIS",
            skill_score=0.0,
            transactions=["Genesis block"],
            reputation_snapshot={}
        )

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, proposer, skill_score, transactions, reputation_snapshot):
        new_block = Block(
            index=len(self.chain),
            previous_hash=self.get_last_block().hash,
            proposer=proposer,
            skill_score=skill_score,
            transactions=transactions,
            reputation_snapshot=reputation_snapshot
        )
        self.chain.append(new_block)
        return new_block

    def is_valid(self):
        for i in range(1, len(self.chain)):
            current  = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True


# ─────────────────────────────────────────
# MODULE 2: Challenge Generator (minimal)
# ─────────────────────────────────────────

def generate_challenge(difficulty_tier):
    """
    Phase 2 (minimal): find a number whose square is divisible
    by the tier-based divisor. Complexity scales with tier.
    Phase 3 will replace this with richer task types.
    """
    target_divisor = difficulty_tier * 7
    search_limit   = difficulty_tier * 500
    return {
        "type"    : "divisibility_search",
        "divisor" : target_divisor,
        "limit"   : search_limit,
        "tier"    : difficulty_tier
    }


# ─────────────────────────────────────────
# MODULE 3: Node
# ─────────────────────────────────────────

class Node:
    """Simulates a miner node with a persistent reputation counter."""

    def __init__(self, node_id, skill_level=1.0):
        self.node_id     = node_id
        self.skill_level = skill_level   # 0.5–1.0: models real-world capability
        self.reputation  = 0             # global persistent counter (floor = 0)

    def solve(self, challenge):
        """
        Attempt the challenge.
        Returns (is_correct, solve_time_seconds, answer).
        """
        start    = time.time()
        divisor  = challenge["divisor"]
        limit    = challenge["limit"]
        delay    = (1.0 / self.skill_level) * 0.01
        result   = None

        for n in range(1, limit + 1):
            time.sleep(delay * random.uniform(0.8, 1.2))
            if (n * n) % divisor == 0:
                result = n
                break

        elapsed    = time.time() - start
        is_correct = result is not None
        return is_correct, elapsed, result

    def update_reputation(self, is_correct):
        """
        +1 for correct solution, -1 for wrong/timeout.
        Clamped at floor = 0 to prevent negative reputation.
        """
        if is_correct:
            self.reputation += 1
        else:
            self.reputation = max(0, self.reputation - 1)


# ─────────────────────────────────────────
# MODULE 4: Skill Evaluator
# ─────────────────────────────────────────

# Updated weights — must sum to 1.0
W1 = 0.35   # Accuracy
W2 = 0.30   # Efficiency
W3 = 0.20   # Difficulty
W4 = 0.15   # Reputation

def accuracy_score(is_correct, partial=False):
    """A(n): 1.0 correct | 0.5 partial | 0.0 wrong/timeout"""
    if is_correct:
        return 1.0
    elif partial:
        return 0.5
    return 0.0

def efficiency_score(t_n, t_min, t_max):
    """E(n) = 1 - (tn - tmin)/(tmax - tmin). Guard for tie."""
    if t_max == t_min:
        return 1.0
    return 1.0 - (t_n - t_min) / (t_max - t_min)

def reputation_score(rep_n, rep_min, rep_max):
    """
    R(n) = (rep_n - rep_min) / (rep_max - rep_min)
    Normalised 0.0–1.0 across all nodes this round.
    Guard: if all reputations are equal (incl. all zero), R(n) = 1.0
    """
    if rep_max == rep_min:
        return 1.0
    return (rep_n - rep_min) / (rep_max - rep_min)

def compute_skill_score(a, e, d, r):
    """PoSk_Score = w1*A + w2*E + w3*D + w4*R"""
    return W1 * a + W2 * e + W3 * d + W4 * r


# ─────────────────────────────────────────
# MODULE 5: Consensus Manager
# ─────────────────────────────────────────

def run_consensus_round(nodes, blockchain, difficulty_tier=3):
    """
    One full PoSk consensus round:
      1. Generate challenge
      2. All nodes attempt it
      3. Compute skill scores (A, E, D, R)
      4. Update reputations
      5. Winner proposes block
    """
    print(f"\n{'═'*60}")
    print(f"  ROUND — Difficulty Tier: {difficulty_tier}")
    print(f"{'═'*60}")

    challenge = generate_challenge(difficulty_tier)
    print(f"  Challenge : {challenge['type']} "
          f"(divisor={challenge['divisor']}, limit={challenge['limit']})")

    # Step 1: Each node solves independently
    results = []
    for node in nodes:
        is_correct, elapsed, answer = node.solve(challenge)
        results.append({
            "node"       : node,
            "node_id"    : node.node_id,
            "is_correct" : is_correct,
            "time"       : elapsed,
            "answer"     : answer,
            "rep_before" : node.reputation        # snapshot before update
        })
        status = "✓" if is_correct else "✗"
        print(f"  {status}  {node.node_id:<6}  "
              f"time={elapsed:.4f}s  answer={answer}  "
              f"rep={node.reputation}")

    # Step 2: Normalisation ranges
    correct_results = [r for r in results if r["is_correct"]]
    times = ([r["time"] for r in correct_results]
             if correct_results else [r["time"] for r in results])
    t_min, t_max = min(times), max(times)

    reps    = [r["rep_before"] for r in results]
    rep_min = min(reps)
    rep_max = max(reps)

    # Step 3: Compute scores
    print(f"\n  {'Node':<8} {'A':>5} {'E':>6} {'D':>4} {'R':>6} {'Score':>8}")
    print(f"  {'-'*45}")

    for r in results:
        a     = accuracy_score(r["is_correct"])
        e     = efficiency_score(r["time"], t_min, t_max)
        d     = difficulty_tier
        rep_r = reputation_score(r["rep_before"], rep_min, rep_max)
        score = compute_skill_score(a, e, d, rep_r)
        r["score"] = score
        r["R"]     = rep_r
        print(f"  {r['node_id']:<8} {a:>5.1f} {e:>6.3f} {d:>4} "
              f"{rep_r:>6.3f} {score:>8.4f}")

    # Step 4: Update reputations AFTER scoring
    for r in results:
        r["node"].update_reputation(r["is_correct"])

    print(f"\n  Reputation after round:")
    for node in nodes:
        print(f"    {node.node_id}: {node.reputation}")

    # Step 5: Select winner and add block
    winner = max(results, key=lambda r: r["score"])
    print(f"\n  Winner → {winner['node_id']}  (score={winner['score']:.4f})")

    rep_snapshot = {node.node_id: node.reputation for node in nodes}
    new_block = blockchain.add_block(
        proposer=winner["node_id"],
        skill_score=winner["score"],
        transactions=[f"TX_round_{len(blockchain.chain)}"],
        reputation_snapshot=rep_snapshot
    )
    print(f"  Block #{new_block.index} added.  Hash: {new_block.hash[:24]}...")
    return winner


# ─────────────────────────────────────────
# MAIN — Phase 2 Demo (1 round)
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("  PoSk Phase 2 — Prototype v2 (with Reputation)")
    print("  " + "─" * 46)

    nodes = [
        Node("N1", skill_level=1.0),    # fast, capable
        Node("N2", skill_level=0.75),   # medium
        Node("N3", skill_level=0.5),    # slower
    ]

    blockchain = Blockchain()
    print("  Blockchain initialised. Genesis block created.")

    # Phase 2: single round, difficulty tier 3
    run_consensus_round(nodes, blockchain, difficulty_tier=3)

    # Chain integrity
    print(f"\n  Chain valid: {blockchain.is_valid()}")
    print(f"\n  ── Final Chain ──")
    for block in blockchain.chain:
        print(block)
