"""
posk/commit_reveal.py
=====================
MODULE 3 — Commit-Reveal Scheme
Prevents nodes from copying each other's answers after seeing peer solutions.

Protocol:
  PHASE 1 — COMMIT
    Each node computes:
        commitment = SHA-256( str(answer) || salt )
    where salt is a freshly generated 256-bit random string.
    The node broadcasts ONLY the commitment hash to the network.
    The answer and salt remain private.

  PHASE 2 — REVEAL
    Once ALL commitments are collected (no node can change its answer
    without being detected), each node broadcasts (answer, salt).

  VERIFICATION
    The consensus manager re-computes:
        expected = SHA-256( str(revealed_answer) || revealed_salt )
    If expected == commitment  →  node is honest, answer accepted
    If expected != commitment  →  node tampered, DISQUALIFIED this round

Security guarantee:
  - Pre-image resistance of SHA-256 makes it computationally infeasible
    to reverse a commitment and find the answer before reveal.
  - The 256-bit salt prevents brute-force guessing even for small answer
    spaces (e.g. a node can't try all Collatz answers 1–1000).
  - Binding: once a commitment is broadcast, the node cannot change its
    answer without the hash mismatch being caught in verification.
"""

import hashlib
import random


def generate_salt():
    """
    Generate a cryptographically random 256-bit salt as a hex string.
    Using SHA-256 of a random 256-bit integer gives us a uniformly
    distributed, collision-resistant salt.
    """
    return hashlib.sha256(str(random.getrandbits(256)).encode()).hexdigest()


def commit(answer, salt=None):
    """
    COMMIT PHASE
    ─────────────
    Compute a binding commitment to 'answer' using 'salt'.

    If salt is not provided, a fresh one is generated automatically.
    The node should store both answer and salt privately after committing.

    Returns:
      commitment : str  — the SHA-256 hash to broadcast publicly
      salt       : str  — the secret random string (keep private until reveal)

    Example:
      commitment, salt = commit(42)
      # broadcast 'commitment' to the network
      # keep 'salt' and answer=42 private
    """
    if salt is None:
        salt = generate_salt()

    # Concatenate answer (as string) with salt before hashing
    # This binds the node to exactly this answer value
    raw        = f"{answer}{salt}"
    commitment = hashlib.sha256(raw.encode()).hexdigest()
    return commitment, salt


def verify(commitment, revealed_answer, revealed_salt):
    """
    REVEAL VERIFICATION
    ────────────────────
    Re-compute the commitment from the revealed values and compare.

    Returns:
      True   — commitment matches, node is honest
      False  — commitment mismatch, node tampered with its answer

    This is called by the Consensus Manager after all nodes have revealed.
    The Consensus Manager only accepts answers where this returns True.
    """
    expected, _ = commit(revealed_answer, revealed_salt)
    return expected == commitment


def tamper_detect_report(node_id, commitment, revealed_answer, revealed_salt):
    """
    Convenience wrapper used by the Consensus Manager for logging.
    Returns a dict with full details for the execution log.
    """
    is_honest  = verify(commitment, revealed_answer, revealed_salt)
    expected, _= commit(revealed_answer, revealed_salt)
    return {
        "node_id"        : node_id,
        "honest"         : is_honest,
        "commitment"     : commitment[:20] + "...",
        "revealed_answer": revealed_answer,
        "recomputed_hash": expected[:20] + "...",
        "verdict"        : "PASS" if is_honest else "TAMPERED — DISQUALIFIED",
    }