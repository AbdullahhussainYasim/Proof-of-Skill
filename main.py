"""
main.py
=======
PoSk Phase 3 — Simulation Entry Point

Ties all modules together:
  posk/blockchain.py    → Block, Blockchain
  posk/challenge.py     → generate_challenge
  posk/commit_reveal.py → commit, verify
  posk/node.py          → Node
  posk/evaluator.py     → score_all_nodes
  posk/consensus.py     → run_round, get_difficulty
  posk/benchmarker.py   → Benchmarker
  posk/logger.py        → Logger

Run:
    python main.py

Output:
  - Terminal: full round-by-round execution log
  - logs/execution_log.txt  — same output saved to file
  - results/metrics.json    — raw benchmark data (JSON)
"""

from posk.blockchain  import Blockchain
from posk.node        import Node
from posk.consensus   import run_round, get_difficulty
from posk.benchmarker import Benchmarker
from posk.logger      import Logger

# ── Simulation configuration ─────────────────────────────────────────────────
NUM_ROUNDS = 10

# Node roster:
#   N1 — top performer,   skill=1.00
#   N2 — strong,          skill=0.85
#   N3 — medium,          skill=0.70
#   N4 — weaker,          skill=0.55
#   N5 — cheating node,   skill=0.90, cheat=True
#         → demonstrates commit-reveal tamper detection every round
NODES = [
    Node("N1", skill_level=1.00),
    Node("N2", skill_level=0.85),
    Node("N3", skill_level=0.70),
    Node("N4", skill_level=0.55),
    Node("N5", skill_level=0.90, cheat=True),
]


def main():
    # ── Initialise infrastructure ─────────────────────────────────────────────
    logger      = Logger(log_dir="logs")
    blockchain  = Blockchain()
    benchmarker = Benchmarker(nodes=NODES, output_dir="results")

    HEADER = "═" * 64
    intro = (
        f"\n{HEADER}\n"
        f"  Proof of Skill (PoSk)  —  Phase 3 Simulation\n"
        f"  Multi-File Architecture  |  10 Rounds  |  Commit-Reveal\n"
        f"  3 Challenge Types  |  Dynamic Difficulty  |  Benchmarking\n"
        f"{HEADER}"
    )
    print(intro)
    logger.write_line(intro)

    nodes_info = "  Nodes: " + "  |  ".join(
        f"{n.node_id}(skill={n.skill_level}{'  CHEATER' if n.cheat else ''})"
        for n in NODES
    )
    print(nodes_info)
    logger.write_line(nodes_info)

    chain_info = "  Blockchain initialised — Genesis block created."
    print(chain_info)
    logger.write_line(chain_info)

    # ── Multi-round simulation loop ───────────────────────────────────────────
    for round_num in range(1, NUM_ROUNDS + 1):
        tier   = get_difficulty(round_num)
        result = run_round(
            round_num=round_num,
            nodes=NODES,
            blockchain=blockchain,
            difficulty_tier=tier,
            logger=logger
        )
        benchmarker.record(result)

    # ── Chain integrity check ─────────────────────────────────────────────────
    logger.section("CHAIN INTEGRITY VERIFICATION")
    valid, msg = blockchain.is_valid()
    integrity_line = f"  Result : {'✓ PASSED' if valid else '✗ FAILED'}  — {msg}"
    print(integrity_line)
    logger.write_line(integrity_line)

    blocks_line = f"  Blocks : {len(blockchain.chain)}  (genesis + {NUM_ROUNDS} round blocks)"
    print(blocks_line)
    logger.write_line(blocks_line)

    # ── Block-by-block chain summary ──────────────────────────────────────────
    logger.section("BLOCK CHAIN SUMMARY")
    summary = blockchain.summary()
    print(summary)
    logger.write_line(summary)

    # ── Performance report ────────────────────────────────────────────────────
    logger.section("PERFORMANCE BENCHMARKING")
    benchmarker.print_report()

    # ── Save outputs ──────────────────────────────────────────────────────────
    json_path = benchmarker.save_json()
    print(f"  Metrics saved → {json_path}")
    logger.write_line(f"  Metrics saved → {json_path}")

    logger.close()
    print(f"  Execution log → logs/execution_log.txt")


if __name__ == "__main__":
    main()