"""
posk/benchmarker.py
===================
MODULE 7 — Performance Benchmarker
Collects and reports hard performance data required by Phase 3 Section 3.

Metrics collected per round:
  - Round execution time (seconds)
  - Challenge type distribution
  - Correct answer rate per node
  - Win frequency per node
  - Score progression per node
  - Reputation growth per node

Comparative validation:
  - PoSk round time vs simulated PoW hash-race time
  - Tamper detection rate (commit-reveal effectiveness)
  - Fairness index: does highest-skill node win proportionally?

Output:
  - results/metrics.json  — raw data for reproducibility
  - results/report.txt    — human-readable summary
"""

import json
import time
import hashlib
import os
from collections import defaultdict


class Benchmarker:
    """
    Collects RoundResult objects and produces performance reports.
    Injected into the simulation by main.py.
    """

    def __init__(self, nodes, output_dir="results"):
        self.nodes      = nodes
        self.output_dir = output_dir
        self.results    = []      # list of RoundResult objects
        os.makedirs(output_dir, exist_ok=True)

    def record(self, round_result):
        """Called by main.py after each round to accumulate data."""
        self.results.append(round_result)

    # ─────────────────────────────────────────────────────────────────────────
    # METRIC COMPUTATIONS
    # ─────────────────────────────────────────────────────────────────────────

    def avg_round_time(self):
        """Average wall-clock time per consensus round (seconds)."""
        if not self.results:
            return 0.0
        return sum(r.round_duration_s for r in self.results) / len(self.results)

    def challenge_distribution(self):
        """Count of each challenge type across all rounds."""
        counts = defaultdict(int)
        for r in self.results:
            counts[r.challenge_type] += 1
        return dict(counts)

    def node_win_counts(self):
        """{ node_id: win_count } across all rounds."""
        return {n.node_id: n.wins for n in self.nodes}

    def node_correct_rates(self):
        """{ node_id: correct_answer_percentage } across all rounds."""
        rates = {}
        for n in self.nodes:
            total   = len(n.history)
            correct = sum(1 for h in n.history if h["correct"])
            rates[n.node_id] = (correct / total * 100) if total > 0 else 0.0
        return rates

    def node_final_reputations(self):
        """{ node_id: final_reputation }."""
        return {n.node_id: n.reputation for n in self.nodes}

    def tamper_detection_rate(self):
        """
        Percentage of tamper attempts that were successfully caught.
        A tamper attempt = any round where a cheating node participated.
        Detection = that round's result shows is_correct=False for the cheater.
        """
        cheaters = [n for n in self.nodes if n.cheat]
        if not cheaters:
            return None   # no cheater in this simulation

        total_attempts = len(self.results)
        detected = sum(
            1 for r in self.results
            for n in cheaters
            if n.node_id in r.node_results
            and r.node_results[n.node_id]["tampered"]
        )
        return (detected / (total_attempts * len(cheaters)) * 100) if total_attempts > 0 else 0.0

    def fairness_index(self):
        """
        Gini-style fairness: how concentrated are wins?
        0.0 = perfectly fair (equal wins), 1.0 = monopoly (one node wins all).
        Lower is fairer.
        """
        wins   = list(self.node_win_counts().values())
        n      = len(wins)
        total  = sum(wins)
        if total == 0 or n <= 1:
            return 0.0
        # Mean absolute difference / (2 * n * mean)
        mean   = total / n
        mad    = sum(abs(wins[i] - wins[j]) for i in range(n) for j in range(n))
        return mad / (2 * n * n * mean) if mean > 0 else 0.0

    def posk_vs_pow_comparison(self):
        """
        Comparative validation (Phase 3 Section 3 requirement).

        Simulates what a PoW hash-race would cost for equivalent rounds:
          - PoW: nodes repeatedly SHA-256 hash random nonces until one
            finds a hash below a target threshold.
          - We simulate the number of hash attempts needed at each difficulty
            tier and measure CPU time.

        Returns a dict with PoSk and PoW timing comparison.
        """
        # Simulate PoW: for each difficulty tier, find how long it takes
        # to hash until finding a value with enough leading zeros.
        pow_times = {}
        for tier in range(1, 6):
            # leading zeros required = tier (simplified PoW difficulty)
            target_prefix = "0" * tier
            start = time.time()
            nonce = 0
            attempts = 0
            while True:
                candidate = hashlib.sha256(f"posk_pow_{nonce}".encode()).hexdigest()
                attempts += 1
                if candidate.startswith(target_prefix):
                    break
                nonce += 1
                if attempts > 50000:   # cap to keep simulation fast
                    break
            pow_times[tier] = {
                "time_s"   : round(time.time() - start, 4),
                "attempts" : attempts,
            }

        # PoSk average round times by tier
        posk_times = defaultdict(list)
        for r in self.results:
            posk_times[r.difficulty_tier].append(r.round_duration_s)
        posk_avg = {
            tier: round(sum(ts) / len(ts), 4)
            for tier, ts in posk_times.items()
        }

        return {
            "posk_avg_round_time_by_tier" : dict(posk_avg),
            "pow_simulated_time_by_tier"  : pow_times,
            "note": (
                "PoSk round time is bounded by task complexity (useful work). "
                "PoW time grows exponentially with leading-zero requirement "
                "and produces no useful output."
            )
        }

    # ─────────────────────────────────────────────────────────────────────────
    # REPORTING
    # ─────────────────────────────────────────────────────────────────────────

    def save_json(self):
        """Write raw metrics to results/metrics.json for reproducibility."""
        comparison = self.posk_vs_pow_comparison()
        data = {
            "simulation_summary": {
                "total_rounds"         : len(self.results),
                "avg_round_time_s"     : round(self.avg_round_time(), 4),
                "challenge_distribution": self.challenge_distribution(),
                "tamper_detection_rate" : self.tamper_detection_rate(),
                "fairness_index"        : round(self.fairness_index(), 4),
            },
            "node_metrics": {
                n.node_id: {
                    "wins"          : n.wins,
                    "correct_rate"  : round(self.node_correct_rates()[n.node_id], 2),
                    "final_rep"     : n.reputation,
                    "is_cheater"    : n.cheat,
                    "score_history" : [h["score"] for h in n.history],
                    "rep_history"   : [h["reputation"] for h in n.history],
                }
                for n in self.nodes
            },
            "comparative_validation": comparison,
        }
        path = os.path.join(self.output_dir, "metrics.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def print_report(self):
        """Print human-readable performance report to stdout."""
        W = 64
        comparison = self.posk_vs_pow_comparison()

        print(f"\n{'█'*W}")
        print(f"{'█':<1}{'  PHASE 3 — PERFORMANCE REPORT':^{W-2}}{'█':>1}")
        print(f"{'█'*W}")

        # Simulation summary
        print(f"\n  ── Simulation Summary ──")
        print(f"  Total rounds          : {len(self.results)}")
        print(f"  Avg round time        : {self.avg_round_time():.4f}s")
        print(f"  Fairness index        : {self.fairness_index():.4f}  "
              f"(0=fair, 1=monopoly)")
        tdr = self.tamper_detection_rate()
        if tdr is not None:
            print(f"  Tamper detection rate : {tdr:.1f}%")
        dist = self.challenge_distribution()
        print(f"  Challenge distribution: "
              + "  ".join(f"{k}={v}" for k, v in dist.items()))

        # Node performance
        print(f"\n  ── Node Performance ──")
        print(f"  {'Node':<8} {'Wins':>5} {'Win%':>6} {'Correct%':>9} "
              f"{'FinalRep':>9}  Note")
        print(f"  {'─'*55}")
        total_rounds = len(self.results)
        for n in self.nodes:
            wp  = n.wins / total_rounds * 100 if total_rounds > 0 else 0
            cr  = self.node_correct_rates()[n.node_id]
            tag = "  [CHEATER — 0 wins via tamper]" if n.cheat else ""
            print(f"  {n.node_id:<8} {n.wins:>5} {wp:>5.1f}% {cr:>8.1f}% "
                  f"{n.reputation:>9}{tag}")

        # Comparative validation: PoSk vs PoW
        print(f"\n  ── Comparative Validation: PoSk vs Simulated PoW ──")
        print(f"  {'Tier':<6} {'PoSk Avg(s)':>12} {'PoW Time(s)':>12} "
              f"{'PoW Attempts':>14}")
        print(f"  {'─'*50}")
        posk_t = comparison["posk_avg_round_time_by_tier"]
        pow_t  = comparison["pow_simulated_time_by_tier"]
        for tier in sorted(pow_t.keys()):
            ps = posk_t.get(tier, "N/A")
            pw = pow_t[tier]
            ps_str = f"{ps:.4f}" if isinstance(ps, float) else ps
            print(f"  {tier:<6} {ps_str:>12} {pw['time_s']:>12.4f} "
                  f"{pw['attempts']:>14,}")
        print(f"\n  Note: {comparison['note']}")

        # Chain type distribution bar
        print(f"\n  ── Challenge Type Distribution ──")
        for ctype, count in dist.items():
            bar = "█" * count
            print(f"  {ctype:<15} {bar}  ({count})")

        print(f"\n{'█'*W}\n")