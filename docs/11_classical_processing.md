# 11 — Classical Pre/Post Processing

## 11.1 Overview

The quantum circuit is sandwiched between classical computations:

```
┌───────────────┐     ┌──────────────┐     ┌────────────────┐
│  Classical     │     │   Quantum    │     │   Classical     │
│  Preprocessing │────▶│   Circuit    │────▶│  Postprocessing │
│                │     │              │     │                 │
│ • Precompute   │     │ • Shor's     │     │ • Key recovery  │
│   point tables │     │   algorithm  │     │ • Verification  │
│ • Encode QROM  │     │              │     │                 │
└───────────────┘     └──────────────┘     └────────────────┘
```

## 11.2 Preprocessing: Point Table Computation

### 11.2.1 Table Structure

For 64 windows with combined 8-bit addressing:

```
For j = 0 to 63:
  For (i, k) ∈ {0,...,15} × {0,...,15}:
    T[j][(i,k)] = i · [2^{4j}] · P  +  k · [2^{4j}] · Q
```

Total entries: 64 × 256 = **16,384 affine EC points**.

### 11.2.2 Computation Method

**Step 1:** Compute powers of 2 of the base points.
```
P_powers[j] = [2^{4j}] · P    for j = 0, 1, ..., 63
Q_powers[j] = [2^{4j}] · Q    for j = 0, 1, ..., 63

Method: iterative doubling
  P_powers[0] = P
  P_powers[j] = [2^4] · P_powers[j-1] = 16 · P_powers[j-1]
  (4 point doublings per step)

Total: 2 × 63 × 4 = 504 point doublings
```

**Step 2:** Compute multiples.
```
For each j:
  iP[0] = O, iP[1] = P_powers[j], iP[2] = 2·P_powers[j], ..., iP[15] = 15·P_powers[j]
  kQ[0] = O, kQ[1] = Q_powers[j], kQ[2] = 2·Q_powers[j], ..., kQ[15] = 15·Q_powers[j]

  For (i, k):
    T[j][(i,k)] = iP[i] + kQ[k]

Per window: 14 + 14 = 28 point additions (for multiples) + 256 point additions (combinations)
Total: 64 × 284 = 18,176 point additions
```

**Step 3:** Convert to affine coordinates.
```
For each entry (X : Y : Z):
  Compute Z_inv = Z^{-1} mod p    (using extended GCD or Fermat's little theorem)
  x = X · Z_inv^2 mod p
  y = Y · Z_inv^3 mod p

16,384 modular inversions (batched using Montgomery's trick: 1 inversion + 3(n-1) multiplications)
```

### 11.2.3 Classical Computation Cost

| Operation | Count | Time (est.) |
|---|---|---|
| Point doublings | 504 | < 1 ms |
| Point additions | ~18,200 | < 10 ms |
| Modular inversions (batched) | 1 + 49K mul | < 50 ms |
| Affine conversions | 16,384 | < 10 ms |
| **Total preprocessing** | | **< 100 ms** |

This is negligible compared to the quantum circuit runtime.

### 11.2.4 Storage Requirements

```
16,384 points × 2 coordinates × 256 bits = 16,384 × 64 bytes = 1,048,576 bytes = 1 MB
```

### 11.2.5 QROM Encoding

Each table entry (affine point) is encoded as a bit-string for the QROM circuit:

```
encode(x, y) = x₀x₁...x₂₅₅y₀y₁...y₂₅₅    (512-bit string, little-endian)
```

The QROM circuit is parameterized by these classical bit-strings. Each window j gets a QROM circuit hardcoded with its 256 data entries.

## 11.3 Postprocessing: Key Recovery

### 11.3.1 Direct Recovery

After measuring the quantum registers, we obtain (c, d) ∈ Z_n × Z_n satisfying:

```
c · k + d ≡ 0  (mod n)
```

If gcd(c, n) = 1 (which holds with probability 1 − 1/n since n is prime):

```
k ≡ −d · c⁻¹  (mod n)
```

**Computation:**
1. Compute c⁻¹ mod n using the extended Euclidean algorithm: O(log² n) operations
2. Compute k = (−d × c⁻¹) mod n: one modular multiplication
3. Verify: compute kP and check kP = Q

```python
def recover_key(c, d, n, P, Q):
    if c == 0:
        return None  # need another run (probability 1/n ≈ 2^{-256})
    c_inv = modular_inverse(c, n)  # extended GCD
    k = (-d * c_inv) % n
    # Verify
    if scalar_mult(k, P) == Q:
        return k
    else:
        return None  # measurement yielded non-useful result; retry
```

### 11.3.2 Handling Edge Cases

**Case 1: c = 0**
- Probability: 1/n ≈ 2⁻²⁵⁶ (negligible)
- Action: Discard and re-run quantum circuit

**Case 2: Verification fails**
- The measurement may yield a result from a "wrong" coset
- Probability of failure: depends on QFT precision and circuit errors
- Action: Re-run quantum circuit (expected 1-2 additional runs)

**Case 3: Multiple valid solutions**
- Since n is prime, the equation ck + d ≡ 0 has exactly one solution for each valid (c,d)
- No ambiguity

### 11.3.3 Success Probability Analysis

For Shor's algorithm on a cyclic group of prime order n:

```
P(success per run) = Σ_{c≠0} (1/n²) × |Σ_{a: a+ck≡0} 1|²/n²
                   ≥ 1 - O(1/n)
                   ≈ 1 - 2⁻²⁵⁶
```

Each run essentially always succeeds (the failure probability is cryptographically negligible). The main source of failure is **circuit errors** (addressed by error correction, with success probability >99% per run).

**Expected number of runs: 1** (with >99% success probability).

We budget for **2-3 runs** for robustness.

## 11.4 End-to-End Workflow

```
Input:
  P = secp256k1 generator (known)
  Q = target public key (known)
  n = group order (known)

Step 1: [Classical] Precompute point tables (~100 ms)
  T[j][(i,k)] = i · 2^{4j} · P + k · 2^{4j} · Q
  for j ∈ [0,63], (i,k) ∈ [0,15]²

Step 2: [Classical] Compile QROM circuits
  For each window j, generate the QROM circuit from T[j]
  Total circuit description: ~79M gates

Step 3: [Quantum] Execute Shor's circuit
  Initialize |0⟩^6004
  Apply Hadamards to input registers
  Execute windowed scalar multiplication
  Apply QFT to input registers
  Measure → (c, d)

Step 4: [Classical] Recover key
  k = −d · c⁻¹ mod n
  Verify Q = kP
  If verification fails, go to Step 3

Output: Private key k such that Q = kP
```

## 11.5 Implementation: Classical Components

### 11.5.1 Modular Arithmetic Library (Python pseudocode)

```python
class Fp:
    """Field element in F_p for secp256k1."""
    p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

    def __init__(self, value):
        self.v = value % self.p

    def __add__(self, other):
        return Fp(self.v + other.v)

    def __sub__(self, other):
        return Fp(self.v - other.v)

    def __mul__(self, other):
        return Fp(self.v * other.v)

    def inv(self):
        """Modular inverse using Fermat's little theorem."""
        return Fp(pow(self.v, self.p - 2, self.p))

    def __eq__(self, other):
        return self.v == other.v
```

### 11.5.2 EC Point Operations (Python pseudocode)

```python
class ECPoint:
    """Point on secp256k1 in affine coordinates."""

    def __init__(self, x, y, infinity=False):
        self.x = Fp(x) if not isinstance(x, Fp) else x
        self.y = Fp(y) if not isinstance(y, Fp) else y
        self.infinity = infinity

    @staticmethod
    def identity():
        return ECPoint(0, 0, infinity=True)

    def __add__(self, other):
        if self.infinity: return other
        if other.infinity: return self
        if self.x == other.x:
            if self.y == other.y:
                return self.double()
            else:
                return ECPoint.identity()

        lam = (other.y - self.y) * (other.x - self.x).inv()
        x3 = lam * lam - self.x - other.x
        y3 = lam * (self.x - x3) - self.y
        return ECPoint(x3, y3)

    def double(self):
        if self.infinity or self.y.v == 0:
            return ECPoint.identity()
        lam = (Fp(3) * self.x * self.x) * (Fp(2) * self.y).inv()
        x3 = lam * lam - Fp(2) * self.x
        y3 = lam * (self.x - x3) - self.y
        return ECPoint(x3, y3)

    def scalar_mult(self, k):
        result = ECPoint.identity()
        addend = self
        while k > 0:
            if k & 1:
                result = result + addend
            addend = addend.double()
            k >>= 1
        return result
```

### 11.5.3 Table Generation

```python
def generate_tables(P, Q, window_size=4):
    """Generate precomputed point tables for QROM."""
    w = window_size
    num_windows = 256 // w  # 64

    # Compute base point powers
    P_pow = [None] * num_windows
    Q_pow = [None] * num_windows
    P_pow[0] = P
    Q_pow[0] = Q
    for j in range(1, num_windows):
        P_pow[j] = P_pow[j-1]
        Q_pow[j] = Q_pow[j-1]
        for _ in range(w):
            P_pow[j] = P_pow[j].double()
            Q_pow[j] = Q_pow[j].double()

    # Generate combined tables
    tables = []
    for j in range(num_windows):
        table_j = {}
        # Precompute multiples of P_pow[j]
        iP = [ECPoint.identity()]
        for i in range(1, 2**w):
            iP.append(iP[-1] + P_pow[j])
        # Precompute multiples of Q_pow[j]
        kQ = [ECPoint.identity()]
        for k in range(1, 2**w):
            kQ.append(kQ[-1] + Q_pow[j])
        # Combined table
        for i in range(2**w):
            for k in range(2**w):
                table_j[(i, k)] = iP[i] + kQ[k]
        tables.append(table_j)

    return tables
```

### 11.5.4 Key Recovery

```python
def recover_private_key(c, d, n, P, Q):
    """Recover private key from Shor's measurement."""
    if c == 0:
        raise ValueError("c=0: need to re-run quantum circuit")

    # Compute k = -d * c^(-1) mod n
    c_inv = pow(c, n - 2, n)  # Fermat's little theorem (n is prime)
    k = (-d * c_inv) % n

    # Verify
    if P.scalar_mult(k) == Q:
        return k
    else:
        raise ValueError("Verification failed: need to re-run quantum circuit")
```

## 11.6 Testing Strategy

### Unit Tests

```python
# Test 1: Known key recovery
k_known = 12345
P = secp256k1_generator()
Q = P.scalar_mult(k_known)
# Simulate (c, d) where ck + d ≡ 0 (mod n)
c = random.randint(1, n-1)
d = (-c * k_known) % n
assert recover_private_key(c, d, n, P, Q) == k_known

# Test 2: Table correctness
tables = generate_tables(P, Q)
for j in range(64):
    for i in range(16):
        for k in range(16):
            expected = P.scalar_mult(i * 16**j) + Q.scalar_mult(k * 16**j)
            assert tables[j][(i,k)] == expected
```

### Integration Test (Classical Simulation)

For small curves (e.g., secp192r1 or a toy 16-bit curve), run the full algorithm end-to-end with a classical quantum circuit simulator to verify correctness before deploying to quantum hardware.
