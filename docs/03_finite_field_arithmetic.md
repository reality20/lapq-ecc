# 03 — Finite Field Arithmetic

All arithmetic is over F_p where p = 2²⁵⁶ − 4294968273.

## 3.1 Number Representation

### 3.1.1 Binary Encoding

Field elements x ∈ [0, p−1] are stored as 256-bit unsigned integers in little-endian qubit order:

```
|x⟩ = |x₀ x₁ x₂ ... x₂₅₅⟩

where x = Σᵢ xᵢ · 2ⁱ
```

### 3.1.2 Coset Representation (Overflow-Tolerant)

For intermediate computations, we allow a 257-bit representation (one overflow bit) and defer modular reduction:

```
|x⟩₂₅₇ where x ∈ [0, 2p − 1]
```

This avoids conditional subtraction after every addition, batching reductions to save gates.

## 3.2 Modular Addition

### 3.2.1 Algorithm: Add-Compare-Subtract

```
ModAdd(|a⟩, |b⟩, |0⟩_carry):
  1. Ripple-carry add:  |a⟩ → |a + b⟩₂₅₇  (257-bit result, carry into overflow)
  2. Compare: compute flag = (a + b ≥ p)
  3. Conditional subtract: if flag, subtract p
  4. Uncompute flag
  Result: |a + b mod p⟩₂₅₆
```

### 3.2.2 Optimized Addition Using Special p

Since p = 2²⁵⁶ − c with c = 4294968273 < 2³³:

**Subtraction of p** is equivalent to **addition of c** with borrow from bit 256:

```
Subtract p from x:
  x − p = x − 2²⁵⁶ + c = (x + c) with bit 256 cleared
```

This makes the conditional subtraction cheaper — we only need a 33-bit addition of c rather than a full 256-bit subtraction.

### 3.2.3 Circuit

```
|a₀...a₂₅₅⟩ ─────────────┬──[Ripple Add]──┬──[Compare ≥p]──[CondSub p]──▶ |a+b mod p⟩
|b₀...b₂₅₅⟩ ─────────────┘                │
|0⟩ (carry)  ──────────────────────────────┘
|0⟩ (flag)   ─────────────────────────────────[computed]──[uncomputed]──▶ |0⟩
```

### 3.2.4 Resource Count

| Resource | Count |
|---|---|
| Qubits (input) | 2 × 256 = 512 |
| Ancilla qubits | 2 (carry + flag) |
| Toffoli gates | 256 (adder) + 33 (compare+subtract) ≈ 289 |
| CNOT gates | ~512 |
| Depth | ~260 |

## 3.3 Modular Subtraction

Modular subtraction a − b mod p is computed as:

```
ModSub(a, b) = ModAdd(a, p − b) = ModAdd(a, (2²⁵⁶ − c) − b)
```

Alternatively, compute a − b, and if the result is negative (borrow out = 1), add p:

```
ModSub(|a⟩, |b⟩):
  1. Ripple-carry subtract: |a⟩ → |a − b⟩ with borrow flag
  2. If borrow: add p (i.e., add 2²⁵⁶ − c)
  3. Uncompute borrow flag
```

Cost is identical to ModAdd: ~289 Toffoli gates.

## 3.4 Modular Multiplication

This is the most critical and expensive primitive, appearing hundreds of millions of times in the full circuit.

### 3.4.1 Schoolbook Multiplication + Modular Reduction

**Step 1: Full multiplication** a × b → 512-bit product

Using the shift-and-add method (quantum-compatible):

```
For i = 0 to 255:
  If b_i = 1:  accumulator += a << i
```

Each iteration is a **controlled addition** of a shifted value, requiring:
- 1 controlled 256-bit addition per bit of b
- Total: 256 controlled additions

**Step 2: Modular reduction** of 512-bit result modulo p

Using the special structure p = 2²⁵⁶ − c:

```
Split result = r_hi · 2²⁵⁶ + r_lo  (r_hi: 256 bits, r_lo: 256 bits)
result mod p ≡ r_lo + c · r_hi  (mod p)
```

Since c < 2³³, the product c · r_hi is at most 289 bits. We then reduce again:

```
Split (r_lo + c · r_hi) = s_hi · 2²⁵⁶ + s_lo
result mod p ≡ s_lo + c · s_hi  (mod p)
```

At most 3 iterations of this reduction suffice (since c · s_hi shrinks each time).

### 3.4.2 Resource Count (Schoolbook)

| Resource | Count |
|---|---|
| Qubits (inputs) | 2 × 256 = 512 |
| Product register | 512 |
| Ancilla (reduction) | 256 + 33 = 289 |
| Toffoli gates | 256 × 256 = 65,536 (multiply) + ~1,000 (reduce) ≈ 66,536 |
| CNOT gates | ~131,000 |
| Depth | ~66,000 |

### 3.4.3 Karatsuba Multiplication (Optimization)

For a 256-bit multiplication, we apply **one level of Karatsuba** decomposition:

Split a = a₁·2¹²⁸ + a₀, b = b₁·2¹²⁸ + b₀.

```
a × b = a₁b₁ · 2²⁵⁶ + ((a₀+a₁)(b₀+b₁) − a₀b₀ − a₁b₁) · 2¹²⁸ + a₀b₀
```

This requires 3 multiplications of 128-bit numbers instead of 1 multiplication of 256-bit numbers, reducing the Toffoli count by ~25%:

| Method | Toffoli Gates |
|---|---|
| Schoolbook 256×256 | 65,536 |
| 1-level Karatsuba | ~49,152 |
| 2-level Karatsuba | ~41,472 |

We use **1-level Karatsuba** (3 × 128-bit schoolbook multiplications) as the default, yielding ~49,152 Toffoli gates per multiplication.

### 3.4.4 Montgomery Multiplication (Alternative)

Montgomery multiplication replaces trial division by p with division by 2²⁵⁶ (which is free in binary). Elements are stored in Montgomery form: ā = a · 2²⁵⁶ mod p.

```
MontMul(ā, b̄):
  t = ā × b̄                           (512-bit product)
  u = (t · p⁻¹ mod 2²⁵⁶) mod 2²⁵⁶    (low half correction)
  r = (t + u · p) >> 256               (right shift = free)
  If r ≥ p: r -= p
  Return r̄ = a·b · 2²⁵⁶ mod p
```

**Advantage:** Reduction is shift-based — very circuit-friendly.
**Disadvantage:** Requires conversion to/from Montgomery form at circuit boundaries.

We adopt Montgomery multiplication for the implementation. The conversion overhead (two extra multiplications at the start and end) is negligible relative to the ~30,000+ multiplications performed during scalar multiplication.

## 3.5 Modular Squaring

Squaring a² mod p is a special case of multiplication with both inputs equal. Classically this offers significant savings; quantumly the savings are more modest since we cannot reuse input qubits without violating no-cloning.

We implement squaring as multiplication with a classical copy where possible (when one operand is classical), and as a self-multiplication otherwise.

When the operand is in superposition, squaring costs the same as multiplication: ~49,152 Toffoli gates.

When the operand is classical (known precomputed point coordinates), squaring can be replaced by a classical-controlled addition sequence, reducing to ~256 × 128 = 32,768 Toffoli gates.

## 3.6 Modular Reduction Circuit Detail

The modular reduction of a 512-bit value x modulo p = 2²⁵⁶ − c exploits the identity 2²⁵⁶ ≡ c (mod p):

```
ModReduce512(|x₀...x₅₁₁⟩):

  // x = x_hi · 2²⁵⁶ + x_lo
  // x mod p ≡ x_lo + c · x_hi

  Step 1: Multiply x_hi (256 bits) by c (33 bits)
    → product is at most 289 bits
    Cost: 256 × 33 Toffoli gates (classical c, quantum x_hi)
         = 8,448 Toffoli gates

  Step 2: Add product to x_lo (289-bit + 256-bit addition)
    Cost: ~289 Toffoli gates

  Step 3: Result may exceed p; conditional subtract p
    Cost: ~289 Toffoli gates

  Step 4: Second reduction pass (if result still ≥ 2²⁵⁶)
    Cost: ~322 Toffoli gates (rare, but must handle)

  Total: ~9,348 Toffoli gates for reduction
```

## 3.7 Reversibility Considerations

All circuits above must be **reversible** (unitary) for use in a quantum computer. Key techniques:

1. **Out-of-place computation:** Compute result into fresh ancillae, then CNOT the result to the target, then uncompute the ancillae by running the circuit in reverse.

2. **Bennett's trick for multiplication:**
   ```
   |a⟩|b⟩|0⟩ → |a⟩|b⟩|a·b mod p⟩
   ```
   requires computing the full product, copying the result, then uncomputing the product workspace.

3. **Carry uncomputation:** Ripple-carry adders naturally allow carry uncomputation by running the carry chain in reverse after the sum bits are computed.

See [Chapter 7](07_reversible_computation.md) for a complete treatment.

## 3.8 Summary of Field Arithmetic Costs

| Operation | Toffoli Gates | CNOT Gates | Ancilla Qubits | Depth |
|---|---|---|---|---|
| ModAdd | 289 | 512 | 2 | 260 |
| ModSub | 289 | 512 | 2 | 260 |
| ModMul (Karatsuba) | 49,152 | ~98,000 | 512 | ~49,500 |
| ModSquare | 49,152 | ~98,000 | 512 | ~49,500 |
| ModReduce (512→256) | 9,348 | ~18,000 | 33 | ~9,400 |
| ModMul (Montgomery) | 50,200 | ~100,000 | 512 | ~50,500 |

*ModMul includes reduction. Montgomery adds a small overhead for the reduction step but avoids trial subtraction.*
