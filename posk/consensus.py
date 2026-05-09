"""
posk/consensus.py
=================
MODULE 6 — Consensus Manager
Orchestrates one complete PoSk round with commit-reveal + scoring.

Round sequence:
  1. Generate challenge (random type, scaled difficulty)
  2. SOLVE PHASE     — all nodes solve independently (no communication)
  3. COMMIT PHASE    — all nodes broadcast SHA-256(answer+salt)
  4. REVEAL PHASE    — all nodes reveal (answer, salt)
  5. VERIFY          — consensus manager checks each commitment
  6. SCORE           — evaluator computes A/E/D/R scores
  7. SELECT WINNER   — highest PoSk score proposes block
  8. UPDATE REP      — reputations updated AFTER scoring
  9. ADD BLOCK       — block appended to chain with rep snapshot

Returns a RoundResult dataclass used by benchmarker and logger.
"""

import time
from posk.challenge  import generate_challenge
from posk.commit_reveal import verify, tamper_detect_report
from posk.evaluator  import score_all_nodes


class RoundResult:
    """
    Immutable record of everything that happened in one round.
    Written to the execution log and consumed by the benchmarker.
    """
    __slots__ = [
        "round_num", "difficulty_tier", "challenge_type",
        "correct_answer", "node_results", "winner_id",
        "block_index", "block_hash", "round_duration_s",
    ]

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def run_round(round_num, nodes, blockchain, difficulty_tier, logger=None):
    """
    Execute one complete PoSk consensus round.

    Parameters:
      round_num       : int       — current round number (1-based)
      nodes           : list[Node]— all competing nodes
      blockchain      : Blockchain
      difficulty_tier : int 1–5
      logger          : Logger | None — if provided, writes structured log

    Returns a RoundResult.
    """
    round_start = time.time()
    SEP = "─" * 64

    def log(msg):
        """Write to logger if available, always print to stdout."""
        print(msg)
        if logger:
            logger.write_line(msg)

    log(f"\n{'═'*64}")
    log(f"  ROUND {round_num:>2}  │  Tier: {difficulty_tier}  │  ", )

    # ── Step 1: Generate challenge ────────────────────────────────────────────
    challenge      = generate_challenge(difficulty_tier)
    ctype          = challenge["type"]
    correct_answer = challenge["correct_answer"]

    log(f"  ROUND {round_num:>2}  │  Tier: {difficulty_tier}  │  Type: {ctype.upper()}")
    log(f"{'═'*64}")
    log(f"  Task    : {challenge['description']}")

    prob = challenge["problem"]
    if ctype == "sorting":
        preview = str(prob["sequence"][:6])[:-1] + ", ...]"
        log(f"  Data    : sequence={preview}  len={len(prob['sequence'])}")
    elif ctype == "pattern":
        log(f"  Data    : sequence={prob['sequence']}  → predict next")
    else:
        log(f"  Data    : start={prob['start']}")
    log(f"  {SEP}")

    # ── Step 2: Solve phase (independent, no communication) ──────────────────
    log(f"  [SOLVE PHASE]")
    node_results = {}
    for node in nodes:
        answer, solve_time = node.solve(challenge)
        node_results[node.node_id] = {
            "node"       : node,
            "answer"     : answer,
            "solve_time" : solve_time,
            "rep_before" : node.reputation,
            "tampered"   : False,
            "is_correct" : False,   # set after reveal verification
        }

    # ── Step 3: Commit phase ──────────────────────────────────────────────────
    log(f"  [COMMIT PHASE]  — nodes broadcast SHA-256(answer+salt)")
    commitments = {}
    for node in nodes:
        commitment = node.commit()
        commitments[node.node_id] = commitment
        log(f"    {node.node_id}: {commitment[:24]}...  {'[CHEATER]' if node.cheat else ''}")

    # ── Step 4 & 5: Reveal + verification ─────────────────────────────────────
    log(f"  [REVEAL PHASE]  — nodes reveal (answer, salt) for verification")
    for node in nodes:
        revealed_answer, revealed_salt = node.reveal()
        report = tamper_detect_report(
            node.node_id, commitments[node.node_id],
            revealed_answer, revealed_salt
        )
        r = node_results[node.node_id]

        if not report["honest"]:
            r["tampered"]   = True
            r["is_correct"] = False
            log(f"    {node.node_id}: ⚠  TAMPERED — commitment mismatch — DISQUALIFIED")
        else:
            r["is_correct"] = (revealed_answer == correct_answer)
            status = "✓" if r["is_correct"] else "✗"
            log(f"    {node.node_id}: answer={revealed_answer}  "
                f"expected={correct_answer}  "
                f"time={r['solve_time']:.4f}s  {status}")

    # ── Step 6: Score all nodes ───────────────────────────────────────────────
    score_all_nodes(node_results, difficulty_tier)

    log(f"\n  {'Node':<8} {'A':>5} {'E':>8} {'D':>4} {'R':>8} {'Score':>9}  Note")
    log(f"  {SEP}")
    for nid, r in node_results.items():
        flag = " ⚠ CHEAT" if r["tampered"] else ""
        log(f"  {nid:<8} {r['A']:>5.1f} {r['E']:>8.4f} {r['D']:>4} "
            f"{r['R']:>8.4f} {r['score']:>9.4f}  {flag}")

    # ── Step 7: Select winner ─────────────────────────────────────────────────
    winner_id = max(node_results, key=lambda nid: node_results[nid]["score"])
    winner_r  = node_results[winner_id]
    log(f"\n  ★  Winner → {winner_id}  (score={winner_r['score']:.4f})")
    winner_r["node"].wins += 1

    # ── Step 8: Update reputations (AFTER scoring so this round uses old rep) ─
    for r in node_results.values():
        r["node"].update_reputation(r["is_correct"])

    rep_line = "  |  ".join(f"{n.node_id}={n.reputation}" for n in nodes)
    log(f"  Reputations: {rep_line}")

    # ── Step 9: Add block to chain ────────────────────────────────────────────
    rep_snapshot = {n.node_id: n.reputation for n in nodes}
    block = blockchain.add_block(
        proposer=winner_id,
        skill_score=winner_r["score"],
        transactions=[f"TX_R{round_num}_A", f"TX_R{round_num}_B"],
        reputation_snapshot=rep_snapshot,
        challenge_type=ctype,
        round_number=round_num
    )
    log(f"  Block #{block.index} → Hash: {block.hash[:32]}...")

    # Record history on each node for benchmarker
    for nid, r in node_results.items():
        r["node"].record_round(
            round_num, ctype, r["is_correct"], r["score"]
        )

    round_duration = time.time() - round_start

    return RoundResult(
        round_num=round_num,
        difficulty_tier=difficulty_tier,
        challenge_type=ctype,
        correct_answer=correct_answer,
        node_results=node_results,
        winner_id=winner_id,
        block_index=block.index,
        block_hash=block.hash,
        round_duration_s=round_duration,
    )


def get_difficulty(round_num):
    """
    Dynamic difficulty escalation.
    Tier increases every 2 rounds, cycling 1→2→3→4→5→1→...

    Round  1-2  → Tier 1
    Round  3-4  → Tier 2
    Round  5-6  → Tier 3
    Round  7-8  → Tier 4
    Round  9-10 → Tier 5
    Round 11-12 → Tier 1 (wraps)
    """
    return ((round_num - 1) // 2) % 5 + 1