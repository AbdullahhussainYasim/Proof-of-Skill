"""
posk/blockchain.py
==================
MODULE 1 — Blockchain Layer
Manages block creation, SHA-256 chaining, and integrity verification.

Phase 3 additions vs Phase 2:
  - Block stores challenge_type and round_number for full audit trail
  - is_valid() returns (bool, message) instead of just bool
  - __repr__ updated for multi-file import compatibility
"""

import hashlib
import time


class Block:
    """
    A single immutable record in the PoSk chain.

    Fields:
      index               – block number (0 = genesis)
      timestamp           – Unix time of creation
      previous_hash       – SHA-256 of the preceding block (chain link)
      proposer            – node_id of the round winner
      skill_score         – winner's PoSk score for this round
      transactions        – list of TX strings recorded in this block
      reputation_snapshot – {node_id: reputation} at block creation time
      challenge_type      – which task type was used this round
      round_number        – round index (0 for genesis)
      hash                – SHA-256 of all fields above (self-sealing)
    """

    def __init__(self, index, previous_hash, proposer, skill_score,
                 transactions, reputation_snapshot, challenge_type, round_number):
        self.index               = index
        self.timestamp           = time.time()
        self.previous_hash       = previous_hash
        self.proposer            = proposer
        self.skill_score         = round(skill_score, 6)
        self.transactions        = transactions
        self.reputation_snapshot = reputation_snapshot
        self.challenge_type      = challenge_type
        self.round_number        = round_number
        # Hash must be computed LAST — after all fields are set
        self.hash                = self._compute_hash()

    def _compute_hash(self):
        """
        SHA-256 over a deterministic string representation of all block fields.
        Any single-bit change in any field produces a completely different hash,
        making tampering immediately detectable.
        """
        raw = (
            f"{self.index}"
            f"{self.timestamp}"
            f"{self.previous_hash}"
            f"{self.proposer}"
            f"{self.skill_score}"
            f"{self.transactions}"
            f"{self.reputation_snapshot}"
            f"{self.challenge_type}"
            f"{self.round_number}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self):
        """Serialise block to a plain dict (used by benchmarker and logger)."""
        return {
            "index"               : self.index,
            "timestamp"           : self.timestamp,
            "previous_hash"       : self.previous_hash,
            "proposer"            : self.proposer,
            "skill_score"         : self.skill_score,
            "transactions"        : self.transactions,
            "reputation_snapshot" : self.reputation_snapshot,
            "challenge_type"      : self.challenge_type,
            "round_number"        : self.round_number,
            "hash"                : self.hash,
        }

    def __repr__(self):
        rep_str = ", ".join(f"{k}:{v}" for k, v in self.reputation_snapshot.items())
        return (
            f"\n  ┌─ Block #{self.index}  (Round {self.round_number})"
            f"\n  │  Type      : {self.challenge_type}"
            f"\n  │  Proposer  : {self.proposer}"
            f"\n  │  Score     : {self.skill_score}"
            f"\n  │  TXs       : {self.transactions}"
            f"\n  │  Reps      : {{{rep_str}}}"
            f"\n  │  Hash      : {self.hash[:32]}..."
            f"\n  └─ PrevHash  : {self.previous_hash[:32]}..."
        )


class Blockchain:
    """
    Ordered, append-only list of Blocks linked by SHA-256 hashes.

    Responsibilities:
      - Initialise with a genesis block
      - Accept new blocks from the Consensus Manager
      - Provide integrity verification across the full chain
    """

    def __init__(self):
        self.chain = [self._make_genesis()]

    def _make_genesis(self):
        """
        Genesis block: index=0, all-zero previous_hash, no proposer.
        This is the anchor of the chain — it has no predecessor.
        """
        return Block(
            index=0,
            previous_hash="0" * 64,
            proposer="GENESIS",
            skill_score=0.0,
            transactions=["Genesis block — PoSk Phase 3"],
            reputation_snapshot={},
            challenge_type="none",
            round_number=0
        )

    def get_last(self):
        """Return the most recently appended block."""
        return self.chain[-1]

    def add_block(self, proposer, skill_score, transactions,
                  reputation_snapshot, challenge_type, round_number):
        """
        Create a new Block referencing the current chain tip and append it.
        Returns the newly created block.
        """
        block = Block(
            index=len(self.chain),
            previous_hash=self.get_last().hash,
            proposer=proposer,
            skill_score=skill_score,
            transactions=transactions,
            reputation_snapshot=reputation_snapshot,
            challenge_type=challenge_type,
            round_number=round_number
        )
        self.chain.append(block)
        return block

    def is_valid(self):
        """
        Full chain integrity check — two conditions per block:
          1. block.hash == freshly recomputed SHA-256  (tamper detection)
          2. block.previous_hash == preceding block's hash  (link integrity)

        Returns (True, "Chain intact") or (False, "<error description>").
        """
        for i in range(1, len(self.chain)):
            cur  = self.chain[i]
            prev = self.chain[i - 1]
            # Condition 1: recompute and compare
            if cur.hash != cur._compute_hash():
                return False, f"Block #{i} hash is invalid (data tampered)"
            # Condition 2: chain link
            if cur.previous_hash != prev.hash:
                return False, f"Block #{i} has broken chain link to Block #{i-1}"
        return True, "Chain intact"

    def summary(self):
        """One-line summary of each block for logging."""
        lines = []
        for b in self.chain:
            if b.round_number == 0:
                lines.append(f"  #{b.index:<3} GENESIS")
            else:
                lines.append(
                    f"  #{b.index:<3} R{b.round_number:<2} "
                    f"proposer={b.proposer:<4} "
                    f"type={b.challenge_type:<15} "
                    f"score={b.skill_score:.4f}  "
                    f"hash={b.hash[:16]}..."
                )
        return "\n".join(lines)