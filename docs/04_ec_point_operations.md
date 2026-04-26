# 04 — Elliptic Curve Point Operations

## 4.1 Coordinate System: Jacobian Projective

We represent points in **Jacobian projective coordinates** (X : Y : Z) where the affine point is (X/Z², Y/Z³).

**Rationale:** Jacobian coordinates eliminate field inversions from the point addition and doubling formulas. A modular inversion would require ~256 modular multiplications (via Fermat's little theorem: a⁻¹ = a^{p-2} mod p), making it prohibitively expensive in a quantum circuit. Jacobian coordinates replace each inversion with a few extra multiplications.

**Equivalence class:** (X : Y : Z) ≡ (λ²X : λ³Y : λZ) for any λ ≠ 0.

**Point at infinity:** Represented by Z = 0 (specifically (1 : 1 : 0)).

## 4.2 Point Doubling

For P = (X₁ : Y₁ : Z₁), compute 2P = (X₃ : Y₃ : Z₃):

Since a = 0 for secp256k1, the formulas simplify significantly:

```
A = Y₁²
B = 4·X₁·A
C = 8·A²
D = 3·X₁²                     (since a=0, no a·Z₁⁴ term)

X₃ = D² − 2·B
Y₃ = D·(B − X₃) − C
Z₃ = 2·Y₁·Z₁
```

### Operation Count for Point Doubling

| Step | Operation | Field Ops |
|---|---|---|
| A = Y₁² | 1 squaring | 1S |
| B = 4·X₁·A | 1 multiplication + 2 doublings | 1M |
| C = 8·A² | 1 squaring + 3 doublings | 1S |
| D = 3·X₁² | 1 squaring + 1 addition (mul by 3 = 2x+x) | 1S + 1A |
| X₃ = D² − 2·B | 1 squaring + 1 doubling + 1 subtraction | 1S + 1A |
| Y₃ = D·(B−X₃) − C | 1 subtraction + 1 multiplication + 1 subtraction | 1M + 2A |
| Z₃ = 2·Y₁·Z₁ | 1 multiplication + 1 doubling | 1M |
| **Total** | | **3M + 4S + 4A** |

Where M = multiplication, S = squaring, A = addition/subtraction.

Since S ≈ M in quantum cost (when operands are in superposition), this is approximately **7M + 4A**.

### Quantum Cost of Point Doubling

```
7 × 49,152 (Toffoli per multiplication) + 4 × 289 (Toffoli per addition)
= 344,064 + 1,156
= 345,220 Toffoli gates
≈ 690,440 CNOT gates
```

## 4.3 Mixed Jacobian-Affine Point Addition

When adding a Jacobian point P₁ = (X₁ : Y₁ : Z₁) to an **affine** point P₂ = (x₂, y₂) (i.e., Z₂ = 1), the formulas simplify:

```
U₁ = X₁                 (since Z₂ = 1)
U₂ = x₂ · Z₁²
S₁ = Y₁                 (since Z₂ = 1)
S₂ = y₂ · Z₁³

H  = U₂ − U₁
R  = S₂ − S₁

X₃ = R² − H³ − 2·U₁·H²
Y₃ = R·(U₁·H² − X₃) − S₁·H³
Z₃ = H · Z₁             (since Z₂ = 1)
```

### Operation Count

| Step | Operation | Cost |
|---|---|---|
| Z₁² | 1 squaring | 1S |
| U₂ = x₂·Z₁² | 1 multiplication | 1M |
| Z₁³ = Z₁²·Z₁ | 1 multiplication | 1M |
| S₂ = y₂·Z₁³ | 1 multiplication | 1M |
| H = U₂ − X₁ | 1 subtraction | 1A |
| R = S₂ − Y₁ | 1 subtraction | 1A |
| H² | 1 squaring | 1S |
| H³ = H²·H | 1 multiplication | 1M |
| U₁·H² = X₁·H² | 1 multiplication | 1M |
| R² | 1 squaring | 1S |
| X₃ = R² − H³ − 2·U₁·H² | 2 subtractions + 1 doubling | 2A |
| Y₃ = R·(U₁·H²−X₃) − S₁·H³ | 1 sub + 1 mul + 1 mul + 1 sub | 2M + 2A |
| Z₃ = H·Z₁ | 1 multiplication | 1M |
| **Total** | | **8M + 3S + 5A** |

Approximately **11M + 5A**, or:

```
11 × 49,152 + 5 × 289 = 540,672 + 1,445 = 542,117 Toffoli gates
```

### Why Mixed Addition?

The precomputed points (multiples of P and Q) are **classical** and can be stored in affine coordinates. Only the accumulator point is quantum (Jacobian). This saves 4 multiplications per addition compared to full Jacobian + Jacobian addition.

Furthermore, when the affine point (x₂, y₂) is **classically known** (which it is, since P and Q are public), several of the multiplications become **classical-controlled additions** instead of quantum-quantum multiplications. Specifically:

- U₂ = x₂ · Z₁²: x₂ is classical → cost reduces to controlled-addition sequence
- S₂ = y₂ · Z₁³: y₂ is classical → same optimization

This reduces the effective cost to approximately **9M + 3S + 5A** ≈ **12M + 5A** → ~541,000 Toffoli gates after optimization.

## 4.4 Handling Special Cases

### 4.4.1 Point at Infinity

When the accumulator is the identity (Z₁ = 0), the addition should return P₂. When P₂ is the identity, return P₁.

In the quantum circuit, we handle this with **conditional swaps**:

```
If Z₁ = 0:
  (X₃, Y₃, Z₃) ← (x₂, y₂, 1)    // swap in P₂ (affine → Jacobian)
```

The zero-check on Z₁ is a 256-bit OR gate (256 Toffoli gates in a tree), and the conditional swap uses 3 × 256 = 768 CSWAP gates (768 Toffoli gates).

### 4.4.2 Point Equality (P₁ = P₂)

When U₁ = U₂ and S₁ = S₂ (i.e., P₁ = P₂), we must perform **point doubling** instead of addition.

**Detection:** Check H = 0 and R = 0 simultaneously (two 256-bit comparators = 512 Toffoli gates).

**Resolution:** Conditionally route to the doubling circuit:

```
If H = 0 AND R = 0:
  Use PointDouble(P₁) instead of PointAdd(P₁, P₂)
```

This is implemented as a multiplexer controlled by the detection flag:

```
flag = (H == 0) AND (R == 0)
X₃ = flag ? X₃_double : X₃_add
Y₃ = flag ? Y₃_double : Y₃_add
Z₃ = flag ? Z₃_double : Z₃_add
```

Cost: ~3 × 256 CSWAP = 768 Toffoli gates + 512 for detection + 345,220 for doubling circuit.

### 4.4.3 Point Negation (P₁ = −P₂)

When U₁ = U₂ but S₁ = −S₂ (H = 0, R ≠ 0), the result is the point at infinity.

**Detection:** H = 0 AND R ≠ 0 (reuses H=0 check from above).

**Resolution:** Conditionally set (X₃, Y₃, Z₃) = (1, 1, 0).

Cost: ~256 Toffoli gates for conditional zeroing/setting.

### 4.4.4 Combined Special Case Handling

Total additional cost for all special cases: ~2,800 Toffoli gates per point addition.

In practice, for random points, the probability of encountering P₁ = ±P₂ during the scalar multiplication is negligible (< 2⁻²⁵⁶). However, **correctness requires handling all cases** — the quantum computer operates on superpositions, and even exponentially unlikely branches contribute to the quantum state.

## 4.5 Controlled Point Addition

The scalar multiplication algorithm requires **controlled** point additions, where the addition is conditioned on a qubit:

```
Controlled-PointAdd(ctrl, |R⟩, P_classical):
  If ctrl = 1: |R⟩ → |R + P_classical⟩
  If ctrl = 0: |R⟩ → |R⟩  (unchanged)
```

**Implementation:** Wrap the entire point addition circuit in controlled gates. Since most sub-operations (ModMul, ModAdd) are already expressed in terms of Toffoli and CNOT, adding a control qubit converts:

- Each Toffoli (CCX) → a doubly-controlled Toffoli (C³X), which decomposes into 2 Toffoli + ancillae
- Each CNOT → a Toffoli

**Overhead factor:** Approximately 2× the uncontrolled cost.

**Optimized approach:** Use the **control qubit to gate the input** rather than every gate:

```
1. CSWAP(ctrl, |P_classical⟩, |0⟩)  →  loads P into register if ctrl=1
2. PointAdd(|R⟩, |register⟩)         →  adds 0 (no-op) or P
3. CSWAP(ctrl, |P_classical⟩, |0⟩)  →  unloads
```

Wait — adding 0 (the identity) is NOT a no-op in the standard formulas (it's a special case). Better approach:

```
1. Controlled-load: if ctrl=1, load P into workspace; else load identity O
2. PointAdd(|R⟩, |workspace⟩)
3. Uncompute workspace
```

Or more efficiently, use the **windowed approach** (Chapter 6) which amortizes the control overhead.

## 4.6 Point Negation

For P = (X : Y : Z), the negation is −P = (X : −Y : Z) = (X : p−Y : Z).

**Circuit:**
```
ModNegate(|Y⟩):  |Y⟩ → |p − Y mod p⟩
```

Cost: 289 Toffoli gates (one modular subtraction from a classical constant p).

## 4.7 Summary of EC Operation Costs

| Operation | Multiplications | Toffoli Gates | Ancilla |
|---|---|---|---|
| Point Doubling | 7M + 4A | 345,220 | 512 |
| Mixed Point Addition | 11M + 5A | 542,117 | 512 |
| Special case handling | — | 2,800 | 256 |
| Controlled Point Add | ~22M + 10A | ~1,084,234 | 1,024 |
| Point Negation | 1A | 289 | 2 |
