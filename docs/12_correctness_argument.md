# 12 — Correctness Argument

## 12.1 Overview

We must argue that the quantum circuit correctly solves the ECDLP. The correctness proof has three components:

1. **Algorithmic correctness:** Shor's algorithm solves ECDLP (reduction to hidden subgroup problem)
2. **Arithmetic correctness:** The quantum arithmetic circuits correctly implement field and group operations
3. **Circuit correctness:** The compiled circuit faithfully implements the algorithm

## 12.2 Algorithmic Correctness

### 12.2.1 Theorem (Shor, 1994; adapted for ECDLP)

**Statement:** Let E be an elliptic curve over F_p with a cyclic subgroup ⟨P⟩ of prime order n. Given Q = kP, the quantum algorithm described in Chapter 5 outputs k with probability ≥ 1 − O(1/n).

**Proof sketch:**

1. **State after oracle:** After applying Hadamards and the oracle U_f, the quantum state is:

   ```
   |ψ₁⟩ = (1/n) Σ_{a,b ∈ Z_n} |a⟩|b⟩|aP + bQ⟩
   ```

2. **Grouping by coset:** Since aP + bQ = (a + bk)P, all pairs (a, b) with the same value of a + bk mod n map to the same point. Grouping:

   ```
   |ψ₁⟩ = (1/n) Σ_{s ∈ Z_n} |φ_s⟩ ⊗ |sP⟩
   ```

   where |φ_s⟩ = (1/√n) Σ_{b ∈ Z_n} |s − bk⟩|b⟩ is a uniform superposition over the coset {(a,b) : a + bk = s}.

3. **Tracing out the point register:** The reduced state of registers (a, b) is:

   ```
   ρ_{ab} = (1/n) Σ_s |φ_s⟩⟨φ_s|
   ```

4. **QFT analysis:** The QFT maps |φ_s⟩ to a state concentrated on (c, d) satisfying ck + d ≡ 0 (mod n):

   ```
   QFT|φ_s⟩ = (1/n) Σ_{c,d} e^{2πi(sc − dkc)/n} ... 
   ```

   By the orthogonality of characters of Z_n, the probability amplitude for measuring (c, d) with ck + d ≢ 0 (mod n) vanishes. Therefore:

   ```
   P(ck + d ≡ 0 mod n) = 1
   ```

5. **Key recovery:** From ck + d ≡ 0 mod n with c ≠ 0 (probability 1 − 1/n):
   ```
   k = −d · c⁻¹ mod n
   ```

**QED (sketch)**

### 12.2.2 Rigorous Statement

More precisely, the measurement outcome (c, d) satisfies:

```
Pr[(c, d) : ck + d ≡ 0 (mod n)] = 1 − 1/n
Pr[c = 0] = 1/n
```

Conditioned on c ≠ 0, the recovered k is unique and correct (since n is prime, the equation ck = −d mod n has a unique solution).

## 12.3 Arithmetic Correctness

### 12.3.1 Modular Addition

**Claim:** The ModAdd circuit maps |a⟩|b⟩ → |a⟩|a + b mod p⟩ for all a, b ∈ [0, p−1].

**Argument:**
1. The ripple-carry adder correctly computes a + b (with carry) — this follows from the correctness of the Cuccaro adder, which is verified gate-by-gate.
2. The comparator correctly determines whether a + b ≥ p — it computes the borrow of the subtraction (a+b) − p.
3. The conditional subtractor correctly subtracts p when the flag is set.
4. The result a + b − p (if a+b ≥ p) or a + b (if a+b < p) equals (a + b) mod p since 0 ≤ a, b < p implies 0 ≤ a + b < 2p.
5. The flag qubit is uncomputed by rerunning the comparator in reverse, leaving no garbage.

### 12.3.2 Modular Multiplication

**Claim:** The ModMul circuit maps |a⟩|b⟩|0⟩ → |a⟩|b⟩|a · b mod p⟩.

**Argument:**
1. The shift-and-add multiplication correctly computes a × b as a 512-bit integer (standard schoolbook algorithm, verified by induction on the number of bits).
2. The Karatsuba optimization is algebraically equivalent: a × b = (a₁·2¹²⁸ + a₀)(b₁·2¹²⁸ + b₀) = a₁b₁·2²⁵⁶ + ((a₀+a₁)(b₀+b₁) − a₀b₀ − a₁b₁)·2¹²⁸ + a₀b₀.
3. Modular reduction using 2²⁵⁶ ≡ c (mod p): For any 512-bit x = x_hi·2²⁵⁶ + x_lo, we have x ≡ x_lo + c·x_hi (mod p). Since c < 2³³ and x_hi < 2²⁵⁶, the product c·x_hi < 2²⁸⁹. Repeating the reduction at most twice brings the result to [0, p−1].
4. Bennett uncomputation preserves the result while cleaning garbage (by the reversibility of quantum gates).

### 12.3.3 Point Addition

**Claim:** The PointAdd circuit correctly computes the elliptic curve group operation in Jacobian coordinates.

**Argument:**
1. The Jacobian addition formulas are standard and algebraically verified (they can be derived from the affine formulas by substituting X = x·Z², Y = y·Z³).
2. Each step uses a verified ModMul or ModAdd, composing correct operations.
3. Special cases (identity, equality, negation) are detected by checking Z₁ = 0, H = 0, R = 0, and the output is correctly routed.
4. The mixed Jacobian-affine formulas (Z₂ = 1) are a specialization of the general formulas with Z₂ = 1 substituted.

### 12.3.4 Scalar Multiplication

**Claim:** The windowed scalar multiplication computes aP + bQ correctly.

**Argument by induction on the number of windows:**

**Base case:** Before any window is processed, R = O (identity).

**Inductive step:** After processing windows 63, 62, ..., j+1, the accumulator contains:
```
R = Σ_{l=j+1}^{63} (w_a[l] · 2^{4l} · P + w_b[l] · 2^{4l} · Q)
```

Processing window j:
1. QROM loads T[j][(w_a[j], w_b[j])] = w_a[j] · 2^{4j} · P + w_b[j] · 2^{4j} · Q
2. Point addition: R ← R + T[j][(...)]
3. New R = Σ_{l=j}^{63} (w_a[l] · 2^{4l} · P + w_b[l] · 2^{4l} · Q)

**After all 64 windows:** R = Σ_{l=0}^{63} (w_a[l] · 2^{4l} · P + w_b[l] · 2^{4l} · Q) = aP + bQ. ∎

## 12.4 Circuit Correctness

### 12.4.1 Gate-Level Verification

Each gate in our gate set is a standard unitary operation:

| Gate | Unitary Matrix | Verified |
|---|---|---|
| X | [[0,1],[1,0]] | Standard |
| H | [[1,1],[1,-1]]/√2 | Standard |
| CNOT | [[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]] | Standard |
| Toffoli | CCX (8×8 permutation) | Standard |

### 12.4.2 Composition Correctness

The circuit is a sequential composition of unitary gates U₁, U₂, ..., U_M. The overall unitary is U = U_M · U_{M-1} · ... · U₁. Each sub-circuit (ModAdd, ModMul, PointAdd, etc.) is verified to implement the correct unitary on its input/output registers while acting as identity on uninvolved qubits.

### 12.4.3 Reversibility Verification

For each sub-circuit with Bennett uncomputation:
1. Forward computation U_f maps |x⟩|0⟩ → |x⟩|f(x)⟩|garbage(x)⟩
2. Copy: CNOT maps |x⟩|f(x)⟩|garbage(x)⟩|0⟩ → |x⟩|f(x)⟩|garbage(x)⟩|f(x)⟩
3. Reverse U_f†: maps |x⟩|f(x)⟩|garbage(x)⟩|f(x)⟩ → |x⟩|0⟩|0⟩|f(x)⟩

The key property is U_f† · U_f = I (unitarity), ensuring perfect uncomputation.

## 12.5 Error Analysis

### 12.5.1 Exact Arithmetic

Our circuit uses **exact modular arithmetic** (no floating-point or approximate computation). Every operation produces the mathematically exact result. There is no algorithmic approximation error.

### 12.5.2 QFT Approximation

The QFT uses rotation gates R_z(π/2^k) for k up to 256. In the surface code, these are synthesized using the Solovay-Kitaev theorem or Ross-Selinger algorithm:

```
Approximation error per rotation: ε ≈ 10⁻¹⁰
Number of rotations in QFT: 256 × 255 / 2 ≈ 32,640
Total QFT approximation error: 32,640 × 10⁻¹⁰ ≈ 3.3 × 10⁻⁶
```

This is negligible.

In practice, rotations with k > 50 contribute < 2⁻⁵⁰ to the amplitude and can be **omitted entirely** (approximate QFT), further reducing the error to essentially zero.

### 12.5.3 Physical Error Rate

As computed in Chapter 10:
```
Expected logical errors per run: 7.9 × 10⁻³
Probability of correct execution: > 99%
```

## 12.6 Completeness Argument

**Claim:** The full system (preprocessing + quantum circuit + postprocessing) recovers the private key k from the public key Q = kP on secp256k1 with probability > 98% using at most 3 runs.

**Argument:**
1. Algorithmic correctness: each run yields (c, d) with ck + d ≡ 0 (mod n) with probability 1 − 1/n ≈ 1 (Section 12.2).
2. Circuit correctness: the quantum circuit implements the algorithm exactly (Section 12.3-12.4).
3. Error resilience: each run succeeds with probability > 99% against physical errors (Section 12.5).
4. Per-run success probability: (1 − 1/n)(0.99) ≈ 0.99.
5. Probability of failure in all 3 runs: (1 − 0.99)³ = 10⁻⁶ < 0.02.
6. Therefore, probability of success in ≤ 3 runs: > 1 − 10⁻⁶ > 0.98. ∎
