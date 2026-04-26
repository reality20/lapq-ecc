# 02 — Architecture Overview

## 2.1 High-Level Circuit Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUANTUM ECDLP SOLVER                         │
│                                                                 │
│  ┌──────────┐  ┌───────────────────────┐  ┌──────────┐         │
│  │  Input    │  │   Elliptic Curve      │  │  QFT +   │         │
│  │  Register │─▶│   Scalar Mult Oracle  │─▶│  Measure │─▶ (c,d)│
│  │  Prep     │  │   f(a,b) = aP + bQ   │  │          │         │
│  └──────────┘  └───────────────────────┘  └──────────┘         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Classical Post-Processing                    │   │
│  │  (c,d) → k = −d·c⁻¹ mod n → private key                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 2.2 Register Architecture

The quantum computer uses ~6,004 logical qubits organized as follows:

```
┌─────────────────────────────────────────────────────────┐
│ Register A  (256 qubits) — scalar a, input to QFT      │
├─────────────────────────────────────────────────────────┤
│ Register B  (256 qubits) — scalar b, input to QFT      │
├─────────────────────────────────────────────────────────┤
│ Point Register X  (256 qubits) — x-coordinate (Jacobian)│
├─────────────────────────────────────────────────────────┤
│ Point Register Y  (256 qubits) — y-coordinate (Jacobian)│
├─────────────────────────────────────────────────────────┤
│ Point Register Z  (256 qubits) — z-coordinate (Jacobian)│
├─────────────────────────────────────────────────────────┤
│ Multiplication Workspace (3 × 512 qubits = 1,536)      │
├─────────────────────────────────────────────────────────┤
│ Modular Reduction Workspace (512 qubits)                │
├─────────────────────────────────────────────────────────┤
│ Point Addition Temporaries (6 × 256 = 1,536 qubits)    │
├─────────────────────────────────────────────────────────┤
│ Carry / Ancilla qubits (256 qubits)                    │
├─────────────────────────────────────────────────────────┤
│ Uncomputation Ancillae (352 qubits)                     │
├─────────────────────────────────────────────────────────┤
│ Windowed Lookup Table (256 qubits)                      │
├─────────────────────────────────────────────────────────┤
│ Control / Flag qubits (48 qubits)                       │
├─────────────────────────────────────────────────────────┤
│ TOTAL: ~6,004 logical qubits                            │
└─────────────────────────────────────────────────────────┘
```

## 2.3 Pipeline Overview

The algorithm executes in the following phases:

### Phase 1: Initialization (Depth ~512)
```
|0⟩^256  ──[H⊗256]──▶  |a⟩ = (1/√n) Σ |a_i⟩
|0⟩^256  ──[H⊗256]──▶  |b⟩ = (1/√n) Σ |b_i⟩
|0⟩^768  ──────────────▶  |Point⟩ = |O⟩  (identity)
|0⟩^4724 ──────────────▶  |workspace⟩
```

### Phase 2: Controlled Scalar Multiplication (Depth ~3.0 × 10⁶)
```
For each bit i = 255 downto 0:
  1. Point doubling:  |R⟩ → |2R⟩
  2. Controlled point addition (conditioned on a_i):
     |R⟩ → |R + a_i · 2^i · P⟩
  3. Controlled point addition (conditioned on b_i):
     |R⟩ → |R + b_i · 2^i · Q⟩
  4. Uncompute all temporaries
```

With windowed optimization (w=4), this becomes ~128 iterations instead of 512, each involving table lookups and a single point addition.

### Phase 3: Uncompute Output Register (Depth ~3.0 × 10⁶)
The output point register must be uncomputed (disentangled) before QFT. This is achieved by running the inverse of Phase 2.

### Phase 4: Quantum Fourier Transform (Depth ~65,536)
```
|a⟩ ──[QFT_256]──▶ |c⟩
|b⟩ ──[QFT_256]──▶ |d⟩
```

### Phase 5: Measurement
Measure registers to obtain classical values (c, d).

### Phase 6: Classical Post-Processing
Compute k ≡ −d · c⁻¹ (mod n) and verify Q = kP.

## 2.4 Circuit Depth Breakdown

| Phase | Depth | % of Total |
|---|---|---|
| Initialization | 512 | 0.02% |
| Scalar Multiplication | 1,500,000 | 48.4% |
| Uncomputation (reverse) | 1,500,000 | 48.4% |
| QFT | 65,536 | 2.1% |
| Measurement | 1 | ~0% |
| **Total** | **~3,066,049** | **100%** |

## 2.5 Data Flow Diagram

```
     a₂₅₅ a₂₅₄ ... a₁ a₀        b₂₅₅ b₂₅₄ ... b₁ b₀
       │    │        │  │           │    │        │  │
       ▼    ▼        ▼  ▼           ▼    ▼        ▼  ▼
    ┌──────────────────────────────────────────────────┐
    │         Windowed Scalar Multiplication            │
    │                                                  │
    │  For each 4-bit window w of (a,b):               │
    │    1. Address table with w → classical point     │
    │    2. Controlled point add to accumulator        │
    │    3. Point doubling ×4                          │
    │    4. Uncompute table lookup                     │
    │                                                  │
    │  Uses: ModMul, ModAdd, ModReduce sub-circuits    │
    └─────────────────────┬────────────────────────────┘
                          │
                    |R⟩ = |aP + bQ⟩
                          │
                    [Uncompute |R⟩]
                          │
                   |a⟩        |b⟩
                    │          │
                 [QFT₂₅₆]  [QFT₂₅₆]
                    │          │
                    ▼          ▼
                   (c)        (d)
                    │          │
                    ▼          ▼
              k = −d·c⁻¹ mod n
```

## 2.6 Modularity

The circuit is organized into a strict module hierarchy:

```
Level 0 (Primitives):
  ├── Quantum AND (Toffoli)
  ├── Quantum OR
  ├── Quantum NOT (Pauli-X)
  ├── Hadamard
  └── Controlled-NOT (CNOT)

Level 1 (Arithmetic):
  ├── Ripple-Carry Adder (256-bit)
  ├── Comparator (256-bit)
  ├── Controlled Subtractor
  └── Conditional Swap (CSWAP)

Level 2 (Field Arithmetic):
  ├── Modular Adder (mod p)
  ├── Modular Subtractor (mod p)
  ├── Modular Multiplier (mod p)
  ├── Modular Squarer (mod p)
  └── Modular Reduction (special form of p)

Level 3 (EC Operations):
  ├── Jacobian Point Doubling
  ├── Mixed Jacobian-Affine Point Addition
  ├── Point Negation
  └── Controlled Point Addition

Level 4 (Algorithm):
  ├── Window Table Lookup (QROM)
  ├── Windowed Scalar Multiplication
  ├── Forward Oracle
  ├── Reverse Oracle (uncomputation)
  └── QFT (256-bit)

Level 5 (Top-Level):
  └── ECDLP Solver
```
