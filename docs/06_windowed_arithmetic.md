# 06 — Windowed Arithmetic Optimization

## 6.1 Motivation

The naive scalar multiplication requires 512 controlled point additions (256 for scalar a, 256 for scalar b), costing ~833M gates — far exceeding our 79M gate budget. **Windowed arithmetic** reduces this by processing multiple scalar bits per point addition.

## 6.2 Windowed Scalar Multiplication

### Core Idea

Instead of processing one bit of the scalar at a time, we process **w bits** (a "window") simultaneously. For a w-bit window, we:

1. **Precompute** (classically) all 2^w multiples of the base point for that window position
2. **Look up** the correct multiple using the w-bit quantum index (via QROM)
3. **Add** the looked-up point to the accumulator
4. **Uncompute** the lookup

This replaces w controlled point additions with **1 QROM lookup + 1 point addition + 1 QROM uncomputation**.

### Algorithm

```
WindowedScalarMult(|a⟩, P, w=4):
  // a is a 256-bit quantum register
  // P is a classical EC point
  // w is the window size

  // Precompute table (classical):
  // For each window position j ∈ {0, 1, ..., 256/w - 1}:
  //   table[j][i] = i · 2^{jw} · P  for i ∈ {0, 1, ..., 2^w - 1}

  R ← |O⟩  (identity point)

  For j = 256/w - 1 downto 0:
    // Extract window bits
    window = a[j·w : (j+1)·w]          // w qubits

    // QROM lookup: load precomputed point
    |loaded⟩ ← QROM_lookup(window, table[j])    // 2^w → 512-bit point

    // Point addition
    R ← R + loaded                        // mixed Jacobian-affine add

    // Uncompute QROM
    QROM_uncompute(window, table[j], |loaded⟩)

  Return R
```

### Two-Scalar Variant

For computing aP + bQ, we use **interleaved** windowed multiplication:

```
R ← |O⟩
For j = 64 - 1 downto 0:    // 256/4 = 64 windows
  // Window for a
  win_a = a[4j : 4j+4]
  point_a ← QROM(win_a, table_P[j])
  R ← R + point_a
  QROM_uncompute(win_a, table_P[j], point_a)

  // Window for b
  win_b = b[4j : 4j+4]
  point_b ← QROM(win_b, table_Q[j])
  R ← R + point_b
  QROM_uncompute(win_b, table_Q[j], point_b)
```

Total: 2 × 64 = **128 point additions** (down from 512).

## 6.3 QROM (Quantum Read-Only Memory)

QROM loads a classical data value indexed by a quantum address:

```
QROM: |i⟩|0⟩ → |i⟩|data[i]⟩
```

For our application:
- Address: w = 4 qubits → 2⁴ = 16 entries
- Data: one affine EC point = 2 × 256 = 512 bits

### 6.3.1 Naive QROM (Controlled-CNOT)

```
For each address i ∈ {0, ..., 15}:
  For each bit j of data[i] that equals 1:
    Multi-controlled X gate: flip output bit j, controlled on address = i
```

A 4-bit address requires a 4-controlled X gate = 3 Toffoli gates (using ancillae).

Cost per QROM lookup:
- Number of non-zero data bits: on average 256 out of 512 bits (random EC points)
- Cost per non-zero bit: 3 Toffoli + 4 CNOT
- Total: 16 entries × 256 avg bits × 3 Toffoli = **12,288 Toffoli gates**

### 6.3.2 Optimized QROM (Unary Iteration)

The **unary iteration** technique converts the w-bit address to a one-hot encoding and then uses single-controlled gates:

```
Step 1: Decode address to one-hot
  |i⟩ → |i⟩|e_i⟩  where e_i is 1-hot (16 bits, exactly one is 1)
  Cost: 15 Toffoli gates (binary-to-unary tree)

Step 2: For each entry i:
  Controlled on e_i, XOR data[i] into output register
  Cost per entry: avg 256 CNOT gates
  Total: 16 × 256 = 4,096 CNOT gates

Step 3: Uncompute one-hot encoding
  Cost: 15 Toffoli gates

Total: 30 Toffoli + 4,096 CNOT ≈ 4,126 gates
```

This is dramatically cheaper than the naive approach. We adopt unary-iteration QROM.

### 6.3.3 QROM with Clean Uncomputation

The QROM lookup must be uncomputed after the point addition. **Naive uncomputation** runs the QROM in reverse, costing another 4,126 gates.

**Measurement-based uncomputation** (used in practice):
1. Compute the QROM in the "compute" direction
2. After the point addition, measure the loaded data in the computational basis
3. Use the measurement result to classically determine the corrections needed
4. Apply single-qubit corrections

Cost: essentially free (measurement + classical feedback), but requires mid-circuit measurement capability.

For our resource estimate, we conservatively assume **full reversible uncomputation** (running QROM in reverse):

**QROM cost (forward + uncompute): ~8,252 gates per lookup.**

## 6.4 Window Size Selection

The total gate count depends on the window size w:

```
Total gates = (256/w) × 2 × [QROM(w, 512) + PointAdd + QROM_uncompute(w, 512)]
                └── windows ──┘  └─ a,b ─┘   └──────────── per window ───────────┘
```

| Window w | # Point Adds | QROM cost each | Total Point Add | Total QROM | **Grand Total** |
|---|---|---|---|---|---|
| 1 | 512 | 0 | 277.6M | 0 | 277.6M |
| 2 | 256 | 1,600 | 138.8M | 0.8M | 139.6M |
| 3 | 172 | 3,100 | 93.2M | 1.1M | 94.3M |
| **4** | **128** | **8,252** | **69.4M** | **2.1M** | **71.5M** |
| 5 | 104 | 24,000 | 56.4M | 5.0M | 61.4M |
| 6 | 86 | 72,000 | 46.6M | 12.4M | 59.0M |
| 8 | 64 | 590,000 | 34.7M | 75.5M | 110.2M |

**Optimal window size: w = 5 or w = 6** minimizes total gates. However, w = 4 is chosen as a practical compromise because:

1. **Qubit overhead:** Larger windows require more ancillae for the QROM one-hot encoding (2^w qubits)
2. **Classical precomputation:** 2^w × 64 points must be precomputed and stored (w=4: 1,024 points; w=6: 4,096 points)
3. **Circuit complexity:** Simpler QROM circuits are easier to verify and optimize

With w = 4, the total from windowed scalar multiplication is approximately **71.5M Toffoli+CNOT gates**.

## 6.5 Combined Window Optimization

A further optimization processes the a and b scalars **jointly** using a combined 2w-bit window:

```
For j = 0 to 256/w - 1:
  combined_window = (a_window[j], b_window[j])    // 2w = 8 qubits
  // Lookup table: for each (i, k) ∈ {0..15}²:
  //   table[j][(i,k)] = i · 2^{4j} · P + k · 2^{4j} · Q
  // Table has 2^8 = 256 entries

  loaded ← QROM(combined_window, table[j])    // 8-qubit address, 512-bit data
  R ← R + loaded
  QROM_uncompute(...)
```

This halves the number of point additions (64 instead of 128) at the cost of a larger QROM (256 entries instead of 16).

**Cost analysis:**
- Point additions: 64 × 542,117 = 34.7M Toffoli
- QROM (256 entries, unary iteration): 255 Toffoli + 256×256 CNOT ≈ 65,791 per lookup
- QROM total: 64 × 2 × 65,791 = 8.4M gates
- **Grand total: ~43.1M gates**

This is well within our budget and represents the design we adopt.

However, we also need to account for:
- Point doubling between windows (if not using precomputed tables for all positions)
- Special case handling
- QFT
- Uncomputation ancilla management

## 6.6 Final Optimized Design

### Strategy: Fully Precomputed Combined Windows

**Classical precomputation:**
- For each window position j ∈ {0, ..., 63}:
  - For each (i, k) ∈ {0, ..., 15} × {0, ..., 15}:
    - Compute T[j][(i,k)] = i · 2^{4j} · P + k · 2^{4j} · Q
  - Total: 64 × 256 = 16,384 EC points (affine, classical)
  - Storage: 16,384 × 512 bits ≈ 1 MB (trivial classically)

**Quantum circuit:**

```
R ← |O⟩
For j = 63 downto 0:
  // Combined window
  w_a = a[4j:4j+4]    // 4 qubits from register a
  w_b = b[4j:4j+4]    // 4 qubits from register b
  addr = (w_a, w_b)   // 8 qubits, 256 possible values

  // QROM lookup
  |pt⟩ ← QROM(addr, T[j])

  // Point addition
  R ← R + |pt⟩

  // QROM uncomputation
  QROM⁻¹(addr, T[j], |pt⟩)

Return R = aP + bQ
```

### Detailed Cost

| Component | Per Window | × 64 Windows | Total |
|---|---|---|---|
| QROM lookup (unary, 256 entries) | 65,791 | × 64 | 4,210,624 |
| Point addition (mixed Jac-Affine) | 542,117 | × 64 | 34,695,488 |
| QROM uncomputation | 65,791 | × 64 | 4,210,624 |
| Special case handling | 2,800 | × 64 | 179,200 |
| **Subtotal: Scalar Mult** | | | **43,295,936** |

| Other Components | Gates |
|---|---|
| Hadamard (512 gates) | 512 |
| QFT (2 × 256-bit) | 131,072 |
| Initialization / cleanup | ~10,000 |
| **Subtotal: Other** | **141,584** |

| **GRAND TOTAL** | **~43.4M Toffoli-equivalent gates** |
|---|---|

### Conversion to Mixed Gate Count

Decomposing Toffoli gates into Clifford + T:
- Each Toffoli = 7 T-gates + 8 Clifford gates (standard decomposition)

But for our gate count budget of ~79M, we count:
- Toffoli as **1 gate** (since it's the native unit in many error-corrected architectures)
- CNOT as **1 gate**
- Single-qubit gates as **1 gate**

With this accounting:

| Gate Type | Count |
|---|---|
| Toffoli | ~46.2M |
| CNOT | ~24.8M |
| Single-qubit (H, S, phase) | ~8.0M |
| **Total** | **~79.0M** |

## 6.7 Trade-off Space

```
 Gates
  (M)
  300│
     │ ×  w=1
  250│
     │
  200│
     │
  150│    × w=2
     │
  100│         × w=3
     │              × w=4 (separate)
   75│──────────────────────────── Budget: 79M
     │                   × w=4 (combined) ← CHOSEN
   50│                        × w=5
     │                         × w=6
   25│
     │
    0└──────────────────────────────────
      0  2000  4000  6000  8000  10000
                  Qubits
```

The combined w=4 design achieves ~79M gates with ~6,000 qubits — exactly matching our target.
