# Proof of Skill (PoSk) — Phase 3

> **Blockchain Technology Project**  
> Multi-File Architecture | 10 Rounds | Commit-Reveal | 3 Challenge Types | Benchmarking

---

## Team

| Name | Roll Number |
|------|-------------|
| Abdullah Hussain Yasim | BSCS23008 |
| M. Ibrahim Butt | BSCS23086 |
| M. Ammar Bin Talib | BSCS23143 |
| Abdullah Salman | BSCS23053 |

**Mentor:** Prof. M. Umar Janjua &nbsp;|&nbsp; **TA:** Shazaib Cheema

---

## Project Structure

```
posk_phase3/
│
├── main.py                  ← Entry point — run this
│
├── posk/                    ← Core package
│   ├── __init__.py
│   ├── blockchain.py        ← MODULE 1: Block + Blockchain (SHA-256 chaining)
│   ├── challenge.py         ← MODULE 2: Challenge Generator (3 task types)
│   ├── commit_reveal.py     ← MODULE 3: Commit-Reveal scheme
│   ├── node.py              ← MODULE 4: Node (solver + commit/reveal)
│   ├── evaluator.py         ← MODULE 5: Skill Score formula (A/E/D/R)
│   ├── consensus.py         ← MODULE 6: Consensus Manager (full round)
│   ├── benchmarker.py       ← MODULE 7: Performance metrics + PoSk vs PoW
│   └── logger.py            ← MODULE 8: Execution log writer
│
├── logs/
│   └── execution_log.txt    ← Generated on run
│
├── results/
│   └── metrics.json         ← Generated on run (raw benchmark data)
│
└── README.md
```

---

## Requirements

- Python 3.8 or higher
- **No external libraries** — standard library only (`hashlib`, `time`, `random`, `json`, `os`)

---

## How to Run

### 1. Clone / download the project

```bash
git clone https://github.com/<your-repo>/posk_phase3.git
cd posk_phase3
```

### 2. Run the simulation

```bash
python main.py
```

That's it. No pip install, no virtual environment needed.

### 3. Check outputs

| Output | Location | Description |
|--------|----------|-------------|
| Terminal | stdout | Full round-by-round execution log |
| Execution log | `logs/execution_log.txt` | Same output saved to file |
| Metrics | `results/metrics.json` | Raw benchmark data (JSON) |

---

## What Phase 3 Implements

### 1. Multi-Round Loop (10 rounds)
Rounds run with fully persistent node reputation. Difficulty tier escalates dynamically every 2 rounds (Tier 1 → 2 → 3 → 4 → 5 → wrap).

### 2. Three Challenge Types
| Type | Description | Difficulty Scaling |
|------|-------------|-------------------|
| `mathematical` | Collatz sequence step count | Larger starting numbers |
| `sorting` | First out-of-order index in a list | Longer lists |
| `pattern` | Next term in arithmetic/geometric series | Fewer clues shown |

### 3. Commit-Reveal Scheme
```
COMMIT:  commitment = SHA-256( str(answer) + salt )
         Broadcast commitment hash only — answer stays private

REVEAL:  Broadcast (answer, salt) after all commitments collected

VERIFY:  Recompute SHA-256( revealed_answer + revealed_salt )
         Match → honest   |   Mismatch → DISQUALIFIED
```
Node N5 in the simulation is a deliberate cheater — it is caught and disqualified every round, demonstrating the tamper detection.

### 4. Skill Score Formula
```
PoSk_Score(n) = 0.35·A(n) + 0.30·E(n) + 0.20·D + 0.15·R(n)
```

### 5. Performance Benchmarking
- Average round time per difficulty tier
- PoSk vs simulated PoW comparison (hash attempts + CPU time)
- Win counts, correct rates, final reputations per node
- Fairness index (Gini-style concentration measure)
- Tamper detection rate

---

## Skill Score Formula Reference

| Component | Formula | Weight |
|-----------|---------|--------|
| A(n) — Accuracy | 1.0 correct / 0.0 wrong or tampered | 0.35 |
| E(n) — Efficiency | 1 − (tₙ−tₘᵢₙ)/(tₘₐₓ−tₘᵢₙ) | 0.30 |
| D — Difficulty | Tier value ∈ {1,2,3,4,5} | 0.20 |
| R(n) — Reputation | (repₙ−Rₘᵢₙ)/(Rₘₐₓ−Rₘᵢₙ) | 0.15 |

---

## Module Responsibilities

| File | Responsibility |
|------|---------------|
| `blockchain.py` | Block creation, SHA-256 hashing, chain integrity |
| `challenge.py` | Random challenge generation (3 types, 5 tiers) |
| `commit_reveal.py` | SHA-256 commit, salt generation, tamper verification |
| `node.py` | Solve challenges, commit/reveal, track reputation |
| `evaluator.py` | Compute A/E/D/R scores with normalisation guards |
| `consensus.py` | Orchestrate one round end-to-end |
| `benchmarker.py` | Collect metrics, PoSk vs PoW comparison, JSON export |
| `logger.py` | Write execution log to file |
| `main.py` | Wire everything together, run 10-round loop |