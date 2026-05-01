# Proof of Skill (PoSk)
### A Novel Blockchain Consensus Mechanism

> **Blockchain Technology — Final Year Project | Phase 2**  
> BSCS — Department of Computer Science

---

## 👥 Team

| Name | Roll Number |
|------|-------------|
| Abdullah Hussain Yasim | BSCS23008 |
| M. Ibrahim Butt | BSCS23086 |
| M. Ammar Bin Talib | BSCS23143 |
| Abdullah Salman | BSCS23053 |

**Mentor:** Professor M. Umar Janjua &nbsp;|&nbsp; **TA:** Shazaib Cheema

---

## 📌 What is PoSk?

**Proof of Skill (PoSk)** is a blockchain consensus mechanism where nodes earn the right to propose blocks by demonstrating genuine computational skill — not by wasting energy (like PoW) or staking wealth (like PoS).

Each round, nodes compete to solve a challenge. The winner is selected based on a **four-component skill score**:

```
PoSk_Score(n) = w1·A(n) + w2·E(n) + w3·D(n) + w4·R(n)
```

| Component | Meaning | Weight |
|-----------|---------|--------|
| **A(n)** — Accuracy | 1.0 correct / 0.5 partial / 0.0 wrong | 0.35 |
| **E(n)** — Efficiency | Normalised solve speed | 0.30 |
| **D** — Difficulty | Task tier ∈ {1, 2, 3, 4, 5} | 0.20 |
| **R(n)** — Reputation | Persistent historical score | 0.15 |

Reputation increases by 1 for every correct solution and decreases by 1 for every wrong answer (floored at 0), rewarding consistent performers across rounds.

---

## 🗂️ Repository Structure

```
posk/
│
├── posk_phase2_v2.py     ← Phase 2 prototype (all 5 modules)
├── README.md             ← This file
│
└── docs/
    └── PoSk_Phase2_Report_v2.docx   ← Full Phase 2 report
```

> **Phase 3** will split the code into separate module files (blockchain.py, node.py, evaluator.py, etc.)

---

## ⚙️ How to Run

### Requirements

- Python 3.x (no external libraries needed)
- Standard library only: `hashlib`, `time`, `random`

### Run the Phase 2 prototype

```bash
python posk_phase2_v2.py
```

### Expected output

```
  PoSk Phase 2 — Prototype v2 (with Reputation)
  ──────────────────────────────────────────────
  Blockchain initialised. Genesis block created.

  ════════════════════════════════════════════════════════════
  ROUND — Difficulty Tier: 3
  ════════════════════════════════════════════════════════════
  Challenge : divisibility_search (divisor=21, limit=1500)
  ✓  N1      time=0.0312s  answer=21  rep=0
  ✓  N2      time=0.0487s  answer=21  rep=0
  ✗  N3      time=0.0821s  answer=None  rep=0

  Node      A      E    D      R    Score
  ---------------------------------------
  N1      1.0   1.000    3   1.000   1.4000
  N2      1.0   0.000    3   1.000   1.1000
  N3      0.0   0.000    3   1.000   0.7500

  Winner → N1  (score=1.4000)
  Block #1 added.  Hash: a3f92c1d88b04e71ac7d...

  Chain valid: True
```

---

## 🧩 System Architecture

```
┌─────────────────────────────────────────────┐
│              Consensus Round                │
│                                             │
│  [Challenge Generator]                      │
│         │  task + difficulty tier D         │
│         ▼                                   │
│  [Node N1] [Node N2] [Node N3]  ...         │
│         │  solve independently              │
│         ▼                                   │
│  [Skill Evaluator]                          │
│     A(n) · E(n) · D · R(n) → Score         │
│         │                                   │
│         ▼                                   │
│  [Consensus Manager]                        │
│     highest score → block proposer          │
│     update reputations                      │
│         │                                   │
│         ▼                                   │
│  [Blockchain Module]                        │
│     SHA-256 block added to chain            │
│     reputation snapshot stored in block     │
└─────────────────────────────────────────────┘
         │
         └──── repeat next round ────►
```

---

## 📐 Skill Score Formula — Details

### Accuracy A(n)
```
A(n) = 1.0   if solution is fully correct
A(n) = 0.5   if partially correct
A(n) = 0.0   if wrong or timeout
```

### Efficiency E(n)
```
E(n) = 1 - (t_n - t_min) / (t_max - t_min)

Guard: if t_max == t_min → E(n) = 1.0 for all nodes
```

### Difficulty D
```
D ∈ {1, 2, 3, 4, 5}   — same for all nodes in a round
```

### Reputation R(n)
```
R(n) = (rep_n - R_min) / (R_max - R_min)

Guard: if all reputations equal → R(n) = 1.0 for all nodes

Update rule (after each round):
  correct  →  reputation(n) += 1
  wrong    →  reputation(n) = max(0, reputation(n) - 1)
  partial  →  reputation(n) unchanged
```

---

## ✅ Phase 2 — What's Done

- [x] Four-component skill score formula with defined weights
- [x] Five-module system architecture designed
- [x] Working Python prototype (single-file)
- [x] SHA-256 block chaining with integrity verification
- [x] Persistent reputation system per node
- [x] Edge case handling: E(n) tie guard, R(n) all-equal guard
- [x] Reputation floor at 0 (no negative reputation)
- [x] Reputation snapshot stored inside each block

---

## 🔭 Phase 3 — Coming Next

- [ ] Multi-round simulation (10+ rounds)
- [ ] Three distinct challenge types (mathematical, sorting, pattern recognition)
- [ ] Commit-reveal scheme to prevent solution copying
- [ ] Performance graphs (score distribution, win frequency, reputation curves)
- [ ] Benchmark comparison vs simulated PoW
- [ ] Fairness analysis — does reputation cause winner lock-in?
- [ ] Split codebase into separate module files
- [ ] IEEE research paper draft

---

## 🆚 Why PoSk? — Comparison

| Feature | PoW | PoS | **PoSk** |
|---------|-----|-----|---------|
| Energy efficient | ❌ | ✅ | ✅ |
| Wealth independent | ✅ | ❌ | ✅ |
| Useful computation | ❌ | ❌ | ✅ |
| Rewards consistency | ❌ | ❌ | ✅ (reputation) |
| Meritocratic | Partial | ❌ | ✅ |

---

## 📄 License

This project is developed for academic purposes as part of a university blockchain course project.

---

## 📬 Contact

For questions regarding this project, please contact any team member through the university portal.
