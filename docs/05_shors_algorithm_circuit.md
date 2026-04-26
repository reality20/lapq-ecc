# 05 — Shor's Algorithm Circuit

## 5.1 Algorithm Specification

**Input:**
- Generator point P ∈ E(F_p) (classical, publicly known)
- Target point Q = kP ∈ E(F_p) (classical, publicly known)
- Group order n (classical, publicly known)

**Output:**
- Private key k ∈ [0, n−1] such that Q = kP

**Quantum circuit computes:**
```
|0⟩^{2·256} |0⟩^{768} |0⟩^{ancilla}
  ↓ H^{⊗512}
|ψ⟩ = (1/n) Σ_{a,b} |a⟩|b⟩|0⟩
  ↓ Oracle
(1/n) Σ_{a,b} |a⟩|b⟩|aP + bQ⟩
  ↓ Uncompute output register
(1/n) Σ_{a,b} e^{2πi·phase(a,b)} |a⟩|b⟩|0⟩
  ↓ QFT⊗² on registers a,b
|c⟩|d⟩
  ↓ Measure
(c, d)  →  k = −d·c⁻¹ mod n
```

## 5.2 Semi-Classical QFT Optimization

The standard QFT on 256 qubits requires O(256²) = 65,536 controlled rotation gates. We use the **semi-classical QFT** to reduce this dramatically.

### Semi-Classical Approach

Instead of applying the full QFT unitarily, we measure qubits one at a time, using classically-controlled single-qubit rotations on subsequent qubits:

```
Semi-Classical QFT on |a₀ a₁ ... a₂₅₅⟩:
  For i = 255 downto 0:
    1. Apply H to qubit aᵢ
    2. Measure aᵢ → classical bit cᵢ
    3. For j = i-1 downto 0:
         Apply classically-controlled R_z(π/2^{i-j}) to aⱼ based on cᵢ
```

**Advantage:** Only 1 quantum qubit is needed at a time (the rest have been measured). This saves qubits but doesn't change gate count.

**In our design:** We use the full unitary QFT to keep the circuit structure clean, since the qubit savings from semi-classical QFT are small relative to the total (~6,000 qubits).

## 5.3 The Scalar Multiplication Oracle

The core quantum operation computes:

```
U_oracle: |a⟩|b⟩|O⟩ → |a⟩|b⟩|aP + bQ⟩
```

### Decomposition into Controlled Point Operations

Using the binary expansions a = Σᵢ aᵢ·2ⁱ and b = Σᵢ bᵢ·2ⁱ:

```
aP + bQ = Σᵢ aᵢ · 2ⁱP + Σⱼ bⱼ · 2ʲQ
```

The precomputed values 2ⁱP and 2ʲQ are **classical** (known ahead of time).

### Double-and-Add (Naive Approach)

```
R ← O (point at infinity)
For i = 255 downto 0:
  R ← 2R                          (point doubling, unconditional)
  If aᵢ = 1: R ← R + P           (controlled point addition)
  If bᵢ = 1: R ← R + Q           (controlled point addition)
Return R = aP + bQ
```

**Cost per iteration:**
- 1 point doubling: 345,220 Toffoli
- 2 controlled point additions: 2 × 1,084,234 = 2,168,468 Toffoli

**Total (256 iterations):**
- 256 × (345,220 + 2,168,468) = 256 × 2,513,688 ≈ 643.5M Toffoli gates

This exceeds our 79M gate budget by 8×. We must optimize.

### Precomputed Table Approach

Instead of doubling at each step, precompute all 2ⁱP and 2ʲQ classically. Then:

```
R ← O
For i = 0 to 255:
  If aᵢ = 1: R ← R + [2ⁱ]P      (controlled addition of classical point)
  If bᵢ = 1: R ← R + [2ⁱ]Q      (controlled addition of classical point)
```

This eliminates all 256 point doublings but still requires 512 controlled point additions:
- 512 × 542,117 ≈ 277.6M Toffoli gates (using uncontrolled mixed add since we gate the input)

Still too many. We need **windowed** arithmetic → see [Chapter 6](06_windowed_arithmetic.md).

## 5.4 Quantum Phase Estimation View

An equivalent (and more standard) formulation uses quantum phase estimation (QPE) on the unitary:

```
U_P: |R⟩ → |R + P⟩     (point addition by a fixed classical point)
```

The eigenvalues of U_P are e^{2πi·j/n} for j = 0, 1, ..., n−1, with eigenstates being superpositions over the cyclic group ⟨P⟩.

QPE on U_P with the input register initialized to |Q⟩ yields the phase j/n where Q = jP, i.e., j = k.

However, this formulation requires O(n) = O(2²⁵⁶) controlled applications of U_P, which is the same cost as the scalar multiplication approach above. The optimization strategies are equivalent.

## 5.5 Complete Circuit Pseudocode

```python
def ecdlp_circuit(P, Q, n):
    """
    Full quantum circuit for ECDLP on secp256k1.
    P, Q: classical EC points
    n: group order
    Returns: measurement results (c, d)
    """
    # Number of bits
    N = 256

    # === Phase 1: Initialization ===
    a = QuantumRegister(N, init="|0⟩")
    b = QuantumRegister(N, init="|0⟩")
    point = JacobianPointRegister(3 * N, init="|O⟩")  # (X:Y:Z) = (1:1:0)
    workspace = AncillaRegister(4724, init="|0⟩")

    # Hadamard on input registers
    for i in range(N):
        H(a[i])
        H(b[i])

    # === Phase 2: Forward oracle ===
    windowed_scalar_mult(a, b, P, Q, point, workspace)
    # State: (1/n) Σ |a⟩|b⟩|aP+bQ⟩

    # === Phase 3: Uncompute oracle ===
    # Run the oracle in reverse to disentangle the point register
    inverse_windowed_scalar_mult(a, b, P, Q, point, workspace)
    # State: (1/n) Σ e^{iφ(a,b)} |a⟩|b⟩|O⟩

    # Actually, we DON'T uncompute - we measure/discard the point register
    # The QFT extracts the phase information from |a⟩|b⟩

    # === Phase 4: QFT ===
    QFT(a, N)
    QFT(b, N)

    # === Phase 5: Measure ===
    c = measure(a)
    d = measure(b)

    return (c, d)
```

**Correction on Phase 3:** In the standard Shor's ECDLP algorithm, we do NOT uncompute the oracle output. Instead, the point register is simply **discarded** (traced out). The QFT on registers a and b extracts the phase relationship. The measurement of the point register (or equivalently, tracing it out) collapses the state onto a coset of the hidden subgroup, after which the QFT identifies the subgroup generators.

Revised circuit:

```python
def ecdlp_circuit_corrected(P, Q, n):
    N = 256
    a = QuantumRegister(N)
    b = QuantumRegister(N)
    point = JacobianPointRegister(3 * N)
    workspace = AncillaRegister(4724)

    # Hadamard
    apply_hadamard(a)
    apply_hadamard(b)

    # Oracle: compute aP + bQ
    windowed_scalar_mult(a, b, P, Q, point, workspace)

    # QFT on input registers only (point register is traced out)
    QFT(a, N)
    QFT(b, N)

    # Measure
    c = measure(a)  # 256-bit integer
    d = measure(b)  # 256-bit integer

    return (c, d)
```

## 5.6 Number of Runs Required

Each run of the circuit yields a pair (c, d) satisfying:

```
c·k + d ≡ 0 (mod n)    with probability ≈ 1/n per specific (c,d)
```

More precisely, the output satisfies the linear relation ck + d ≡ 0 (mod n) **exactly** (up to measurement statistics). A single successful measurement gives:

```
k ≡ −d · c⁻¹ (mod n)    [if gcd(c, n) = 1]
```

Since n is prime, c = 0 happens with probability 1/n ≈ 2⁻²⁵⁶ (negligible). Thus, a **single run** suffices to recover k with overwhelming probability.

In practice, 2-3 runs are performed for confirmation (verifying Q = kP classically after each run).

## 5.7 Total Gate Count (Before Windowed Optimization)

Using the precomputed table approach (no windowing):

| Component | Toffoli | CNOT | Total |
|---|---|---|---|
| Hadamard (512) | 0 | 0 | 512 |
| 512 controlled point adds | 277.6M | 555M | 832.6M |
| QFT (2 × 256-bit) | 0 | 131K | 131K |
| **Total** | **277.6M** | **555M** | **832.7M** |

This is ~10× our budget. The **windowed approach** (Chapter 6) reduces this to ~79M total gates.
