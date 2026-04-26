# 08 — Qubit Budget & Layout

## 8.1 Detailed Qubit Allocation

### 8.1.1 Input Registers

| Register | Width (qubits) | Purpose |
|---|---|---|
| a (scalar for P) | 256 | Superposition of scalar a; input to QFT |
| b (scalar for Q) | 256 | Superposition of scalar b; input to QFT |
| **Subtotal** | **512** | |

### 8.1.2 Accumulator Point (Jacobian)

| Register | Width (qubits) | Purpose |
|---|---|---|
| X coordinate | 256 | Jacobian X of running sum R |
| Y coordinate | 256 | Jacobian Y of running sum R |
| Z coordinate | 256 | Jacobian Z of running sum R |
| **Subtotal** | **768** | |

### 8.1.3 QROM Output (Affine Point)

| Register | Width (qubits) | Purpose |
|---|---|---|
| x coordinate | 256 | Looked-up affine x |
| y coordinate | 256 | Looked-up affine y |
| **Subtotal** | **512** | |

### 8.1.4 QROM Ancillae

| Register | Width (qubits) | Purpose |
|---|---|---|
| One-hot address | 256 | Unary encoding of 8-bit combined window address |
| Decode tree ancillae | 8 | Binary-to-unary conversion intermediates |
| **Subtotal** | **264** | |

### 8.1.5 Point Addition Workspace

The mixed Jacobian-affine point addition requires temporary field elements:

| Temporary | Width | Lifetime |
|---|---|---|
| Z₁² | 256 | Computed early, used twice, then uncomputed |
| Z₁³ | 256 | Computed early, used once, then uncomputed |
| H = U₂ − U₁ | 256 | Used through most of computation |
| R = S₂ − S₁ | 256 | Used through most of computation |
| H² | 256 | Intermediate |
| H³ | 256 | Intermediate |
| U₁·H² | 256 | Intermediate |
| R² | 256 | Intermediate |
| **Subtotal** | **2,048** | *Max simultaneous: ~1,536* |

Due to sequential reuse of temporaries (later ones are allocated after earlier ones are freed), the peak usage is approximately **1,536 qubits**.

### 8.1.6 Modular Multiplication Workspace

Each ModMul requires:

| Component | Width | Purpose |
|---|---|---|
| Product register (Karatsuba) | 512 | Stores intermediate 512-bit product |
| Partial products (3×) | 3 × 128 = 384 | Three 128-bit sub-products |
| Carry chain | 256 | Addition carries |
| Reduction workspace | 33 | For multiplying by c in reduction |
| **Subtotal** | **1,185** | *Peak: ~768 (with reuse)* |

Only one ModMul executes at a time, so this workspace is shared across all multiplications.

### 8.1.7 Checkpoint Storage

For the √n pebble strategy with 4 checkpoints:

| Component | Width | Purpose |
|---|---|---|
| Checkpoint 1 (Jacobian point) | 768 | Stored intermediate accumulator state |
| Checkpoint 2 | 768 | |
| Checkpoint 3 | 768 | |
| Checkpoint 4 | 768 | |
| **Subtotal** | **3,072** | *Can be reduced with fewer checkpoints* |

**Revision:** 4 checkpoints × 768 = 3,072 qubits is too many. We reduce to **2 checkpoints** (1,536 qubits), accepting ~4× recomputation overhead.

### 8.1.8 Special Case Flags and Control

| Register | Width | Purpose |
|---|---|---|
| Z₁ = 0 flag | 1 | Point-at-infinity detection |
| H = 0 flag | 1 | P₁ = ±P₂ detection |
| R = 0 flag | 1 | P₁ = P₂ vs P₁ = −P₂ |
| Comparison flags | 4 | ModAdd/ModSub overflow |
| Loop control | 6 | Window counter (classical) |
| Phase tracking | 8 | For QFT phase gates |
| Carry ancillae (reusable) | 16 | Ripple-carry adder work bits |
| Miscellaneous | 11 | Buffer/alignment |
| **Subtotal** | **48** | |

## 8.2 Budget Summary

| Category | Qubits | % of Total |
|---|---|---|
| Input registers (a, b) | 512 | 8.5% |
| Accumulator point (X, Y, Z) | 768 | 12.8% |
| QROM output + ancillae | 776 | 12.9% |
| Point addition workspace | 1,536 | 25.6% |
| Multiplication workspace | 768 | 12.8% |
| Checkpoint storage (2×) | 1,536 | 25.6% |
| Flags and control | 48 | 0.8% |
| Padding/alignment | 60 | 1.0% |
| **TOTAL** | **6,004** | **100%** |

## 8.3 Qubit Layout Map

```
Qubit Index:  0                    512       1280     2056     2832     3600     4368    5136    5904  6004
              │─── Input Regs ─────│── Acc ──│─ QROM ─│─ PtAdd ─│─ Mul ──│─ Chk1 ─│─Chk2──│─Ctrl─│─Pad─│
              │     a     │    b   │ X│ Y│ Z │ x│ y│OH│   temps  │  work  │  768   │  768  │  48  │ 60  │
              │    256     │   256  │256│256│256│256│256│264│  1536  │  768  │  768   │  768  │  48  │ 60  │
```

## 8.4 Qubit Reuse Timeline

```
Phase            ──── Init ────┬──── Window 63 ────┬──── Window 62 ────┬─ ... ─┬── QFT ──┬─ Meas ─
                               │                   │                   │       │         │
Input a,b:       [─────────────────────────────────────────────────────────────────QFT────── Meas ]
Accumulator:     [────alloc─── ──── update ──────── ──── update ──────── ... ── discard──────────]
QROM output:     [              alloc──use──free    alloc──use──free    ...                      ]
QROM ancillae:   [              alloc──use──free    alloc──use──free    ...                      ]
PtAdd workspace: [              alloc──use──free    alloc──use──free    ...                      ]
Mul workspace:   [              alloc─use─free (×11 per window)         ...                      ]
Checkpoints:     [       alloc CP1          alloc CP2         ...       free CP2    free CP1     ]
```

Key observations:
- **QROM output** is allocated and freed each window → 512 qubits reused 64 times
- **PtAdd workspace** similarly reused each window
- **Mul workspace** reused ~11 times per window × 64 windows = ~704 reuses
- **Checkpoints** have the longest lifetime, spanning multiple windows

## 8.5 Qubit Quality Requirements

All 6,004 logical qubits must maintain coherence throughout the circuit execution. At a circuit depth of ~3.1 × 10⁶:

| Qubit Type | Coherence Requirement | Error Rate Needed |
|---|---|---|
| Input registers | Full circuit (~3.1M depth) | < 3.2 × 10⁻⁷ per gate |
| Accumulator | ~3.0M depth | < 3.3 × 10⁻⁷ per gate |
| Checkpoints | ~1.5M depth (average) | < 6.7 × 10⁻⁷ per gate |
| Workspace (reused) | ~50K depth per use | < 2 × 10⁻⁵ per gate |

The surface code error correction (Chapter 10) provides logical error rates of ~10⁻¹⁰ per gate, comfortably exceeding all requirements.

## 8.6 Comparison with Prior Work

| Work | Qubits | Gates | Year |
|---|---|---|---|
| Roetteler et al. | 2,330 | 1.26 × 10¹¹ | 2017 |
| Häner et al. | 2,338 | ~10¹⁰ | 2020 |
| Banegas et al. | ~3,000 | ~10⁹ | 2021 |
| Litinski | ~4,000 | ~10⁸ | 2023 |
| **This design** | **6,004** | **7.9 × 10⁷** | **2026** |

Our design trades more qubits for fewer gates, which is favorable for near-term error-corrected quantum computers where gate count (circuit depth × width) determines the dominant error probability and runtime.
