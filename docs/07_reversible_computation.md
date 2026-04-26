# 07 — Reversible Computation & Uncomputation

## 7.1 The Reversibility Requirement

Quantum circuits must be **unitary** (reversible). Every classical computation embedded in a quantum circuit must:

1. Produce no garbage bits (or clean them up)
2. Be invertible — every gate must have a well-defined reverse

This is challenging because classical arithmetic (addition, multiplication, comparison) produces carry bits, intermediate results, and overflow flags that are not part of the final answer.

**The no-cloning theorem** prevents us from simply copying quantum results. We cannot "save a copy" of an intermediate value and then discard the original.

## 7.2 Bennett's Reversible Computation Method

Bennett's trick (1973) converts any irreversible computation into a reversible one with controlled space overhead.

### Basic Version (Compute-Copy-Uncompute)

For a function f: {0,1}ⁿ → {0,1}ᵐ:

```
|x⟩|0⟩ᵐ|0⟩^{garbage}
  ↓  Forward computation
|x⟩|f(x)⟩|garbage(x)⟩
  ↓  Copy result to clean register
|x⟩|f(x)⟩|garbage(x)⟩|f(x)⟩
  ↓  Reverse computation (uncompute)
|x⟩|0⟩ᵐ|0⟩^{garbage}|f(x)⟩
  ↓  Relabel registers
|x⟩|f(x)⟩
```

**Space cost:** The garbage register may be as large as the entire computation's intermediate state.

### Pebble Game Optimization

For sequential computations (like scalar multiplication with 64 steps), the **pebble game** strategy reduces space at the cost of recomputation:

```
Given a chain: f = f₆₄ ∘ f₆₃ ∘ ... ∘ f₁

Naive: store all 64 intermediate results → 64 × (space per step)
Pebble: use O(log 64) = 6 "pebbles" (stored intermediates)
  → recompute steps as needed from the nearest pebble
```

**Trade-off:**
| Strategy | Space (intermediates) | Time (recomputation factor) |
|---|---|---|
| Store all | 64 × S | 1× |
| Pebble (log) | 6 × S | O(log² 64) ≈ 36× |
| Pebble (√) | 8 × S | 2× |
| **Chosen: √n** | **8 × S** | **2×** |

We use the **√n pebble strategy** with 8 checkpoints for 64 windows, giving 2× time overhead but only 8× space for intermediates.

## 7.3 Reversible Modular Addition

The ripple-carry adder is naturally almost reversible:

### Cuccaro Ripple-Carry Adder

```
|a⟩|b⟩|0⟩_carry  →  |a⟩|a+b⟩|carry_out⟩

Forward:
  For i = 0 to n-1:
    carry[i+1] = MAJ(carry[i], a[i], b[i])
  // carry chain computed

  For i = n-1 downto 0:
    (sum[i], carry[i]) = UMA(carry[i], a[i], b[i])
  // sum computed, carries uncomputed

Where:
  MAJ(c,a,b): c ← c⊕a; b ← b⊕a; Toffoli(c,b,a)   [a gets majority]
  UMA(c,a,b): Toffoli(c,b,a); b ← b⊕a; c ← c⊕a    [inverse of MAJ + sum]
```

**Properties:**
- Uses only 1 ancilla qubit (initial carry)
- 2n Toffoli gates + 2n CNOT gates for n-bit addition
- Automatically reversible (run gates in reverse order, flip each gate)

**Modular addition** wraps this with comparison and conditional subtraction:

```
ModAdd(|a⟩, |b⟩):
  1. RippleAdd(a, b)         →  |a+b⟩  (may overflow)
  2. Compare(a+b, p)         →  flag
  3. CondSub(flag, a+b, p)   →  |(a+b) mod p⟩
  4. Uncompute flag          →  clean ancillae
```

## 7.4 Reversible Modular Multiplication

The most complex reversible circuit. We use **out-of-place multiplication** with Bennett uncomputation:

```
ModMul(|a⟩, |b⟩) → |a⟩|a·b mod p⟩:

  Step 1: Compute product into fresh register
    |a⟩|b⟩|0⟩^512 → |a⟩|b⟩|a×b⟩^512
    Using schoolbook shift-and-add (with Karatsuba optimization)

  Step 2: Modular reduction
    |a×b⟩^512 → |a·b mod p⟩^256 |reduction_garbage⟩^256

  Step 3: Copy result to output register
    CNOT^256: |a·b mod p⟩ → |output⟩

  Step 4: Uncompute reduction (reverse of step 2)
    |a·b mod p⟩|reduction_garbage⟩ → |a×b⟩^512

  Step 5: Uncompute multiplication (reverse of step 1)
    |a⟩|b⟩|a×b⟩^512 → |a⟩|b⟩|0⟩^512

  Final state: |a⟩|b⟩|a·b mod p⟩
```

**Key insight:** Steps 4-5 run the computation in reverse, cleaning up all intermediate garbage. The only new information retained is the copied result.

### Cost Accounting

| Step | Toffoli | CNOT | Purpose |
|---|---|---|---|
| Forward multiply | 49,152 | 98,000 | Compute a×b |
| Forward reduce | 9,348 | 18,000 | Reduce mod p |
| Copy result | 0 | 256 | CNOT copy |
| Reverse reduce | 9,348 | 18,000 | Uncompute |
| Reverse multiply | 49,152 | 98,000 | Uncompute |
| **Total** | **117,000** | **232,256** | |

Wait — this counts 2× the forward cost (forward + reverse). Our original estimate of 49,152 per multiplication assumed an **in-place** computation. With reversibility overhead, the true cost is **~117,000 Toffoli gates per modular multiplication**.

**Impact on total gate count:** All previous estimates must be doubled for reversibility. But wait — in the point addition formulas, many multiplications are **sequentially dependent** (output of one feeds into the next), so Bennett's trick applies to the entire point addition, not to each multiplication individually.

### Optimized Reversible Point Addition

Rather than making each ModMul individually reversible, we make the **entire point addition** reversible as a unit:

```
PointAdd_reversible(|R⟩, |P_classical⟩) → |R + P⟩:

  Step 1: Forward computation
    Compute R + P using 11 ModMul + 5 ModAdd
    → produces (X₃, Y₃, Z₃) + garbage

  Step 2: Copy (X₃, Y₃, Z₃) to clean output register
    768 CNOT gates

  Step 3: Reverse computation (uncompute garbage)
    Run step 1 in reverse
    → all workspace returned to |0⟩

  Final: |R + P⟩ in output, workspace clean
```

Total reversible cost: 2 × (forward cost) + 768 CNOT

- Forward cost: 11 × 49,152 + 5 × 289 = 542,117
- Reversible cost: 2 × 542,117 + 768 = **1,085,002** Toffoli-equivalent

This is the number we use in the windowed arithmetic analysis. The ~79M total already accounts for this by including both forward and reverse passes.

## 7.5 Optimized Uncomputation for Sequential Operations

In the windowed scalar multiplication, we perform 64 sequential point additions. The intermediate accumulator states are:

```
R₀ = O → R₁ = R₀ + T[63] → R₂ = R₁ + T[62] → ... → R₆₄ = aP + bQ
```

Using the √n pebble strategy with 8 checkpoints:

```
Checkpoints at windows: 0, 8, 16, 24, 32, 40, 48, 56

Forward pass:
  Compute R₀ → R₈ (store checkpoint)
  Compute R₈ → R₁₆ (store checkpoint)
  ...
  Compute R₅₆ → R₆₄ (final result)

Uncomputation:
  Recompute R₅₆ from checkpoint (8 point additions)
  Uncompute R₆₄ → R₅₆ → ... → R₅₆ (clean workspace)
  Then uncompute R₅₆ checkpoint
  ...repeat for each segment...
```

**Effective time overhead:** 2× (compute forward + compute reverse from checkpoints)
**Space saving:** Only 8 intermediate Jacobian points stored (8 × 768 qubits = 6,144 qubits)

Since 6,144 > our qubit budget for intermediates, we use **4 checkpoints** instead:

```
4 checkpoints × 768 qubits = 3,072 qubits for intermediates
Time overhead: ~3× (some recomputation needed)
```

This fits within our ~6,000 qubit budget.

## 7.6 Ancilla Management Strategy

```
┌─────────────────────────────────────────┐
│          Ancilla Lifecycle              │
│                                         │
│  1. Allocate from pool (clean |0⟩)      │
│  2. Use in computation (dirty)          │
│  3. Uncompute back to |0⟩               │
│  4. Return to pool                      │
│                                         │
│  Pool size: 4,724 qubits               │
│  Max simultaneous dirty: ~2,048         │
│  Reuse factor: ~12× over full circuit   │
└─────────────────────────────────────────┘
```

The ancilla pool is managed as a **stack** (LIFO): the most recently allocated ancillae are the first to be uncomputed and returned. This matches the structure of Bennett uncomputation naturally.

## 7.7 Correctness of Reversible Constructions

**Theorem (Bennett, 1973):** Any computation using space S and time T can be made reversible using space O(S·log T) and time O(T^{1+ε}).

**Our application:** With S = 768 (one EC point), T = 64 (point additions), and the √n pebble strategy:
- Reversible space: O(768 × √64) = O(768 × 8) = 6,144 qubits
- Reversible time: O(64 × 2) = 128 effective point additions

This is consistent with our resource estimates.
