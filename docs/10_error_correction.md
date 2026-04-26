# 10 — Quantum Error Correction

## 10.1 Error Correction Strategy: Surface Code

We use the **rotated surface code** — the leading candidate for fault-tolerant quantum computing. The surface code provides:

- **2D nearest-neighbor connectivity** (physically realizable)
- **High threshold error rate:** ~1% per physical gate
- **Efficient logical operations:** Clifford gates via lattice surgery

### Key Parameters

| Parameter | Value | Justification |
|---|---|---|
| Code distance | d = 23 | Achieves logical error rate ~10⁻¹⁰ per gate |
| Physical error rate (assumed) | p_phys = 10⁻³ | State-of-the-art superconducting qubits |
| Logical error rate (achieved) | p_L ≈ 10⁻¹⁰ | p_L ≈ 0.1 × (p_phys / p_th)^{(d+1)/2} |
| Physical qubits per logical qubit | 2d² = 1,058 | Rotated surface code |

### Logical Error Rate Calculation

The surface code logical error rate scales as:

```
p_L ≈ C × (p_phys / p_threshold)^{⌊(d+1)/2⌋}
```

With p_threshold ≈ 0.01, p_phys = 10⁻³, C ≈ 0.1:

```
p_L ≈ 0.1 × (10⁻³ / 10⁻²)^{12}
    = 0.1 × (0.1)^{12}
    = 0.1 × 10⁻¹²
    = 10⁻¹³
```

This exceeds our requirement of 10⁻¹⁰ per gate, providing a safety margin.

## 10.2 Physical Qubit Count

### Logical-to-Physical Mapping

| Component | Logical Qubits | Physical Qubits per Logical | Physical Qubits |
|---|---|---|---|
| Data qubits | 6,004 | 2 × 23² = 1,058 | 6,352,232 |
| Magic state factories | ~8 factories × ~4,000 physical each | — | 32,000 |
| Routing / spacing | ~20% overhead | — | 1,276,847 |
| **Total physical qubits** | | | **~7,661,079** |

Rounded: **~7.7 million physical qubits.**

### Magic State Distillation

T-gates (and hence Toffoli gates) cannot be implemented transversally in the surface code. They require **magic state distillation**:

1. Prepare noisy T-states (|T⟩ = T|+⟩)
2. Distill using the 15-to-1 protocol: 15 noisy → 1 cleaner
3. Repeat for desired precision

**Distillation factory configuration:**

| Level | Input States | Output States | Error Rate |
|---|---|---|---|
| Level 1 | 15 noisy (p ≈ 10⁻³) | 1 (p ≈ 10⁻⁸) | 35 × p³ |
| Level 2 | 15 Level-1 | 1 (p ≈ 10⁻²⁴) | 35 × p³ |

One level of distillation suffices for our target (10⁻⁸ < 10⁻¹⁰ after accounting for gate count).

**Factory throughput:** Each factory produces ~1 T-state per code cycle (d rounds of syndrome extraction = 23 μs at 1 μs per round).

**T-gate demand:** 323.4M T-gates over 3.1M depth levels ≈ 104 T-gates per depth level.

**Factories needed:** ⌈104 / 1⌉ = 104 factories operating in parallel. However, not all depth levels require T-gates uniformly. With buffering:

**8 factories** producing T-states at ~13× the consumption rate, with a buffer of ~1,000 T-states, suffice for continuous operation.

## 10.3 Surface Code Lattice Surgery

Logical CNOT and Toffoli gates are implemented via **lattice surgery** — merging and splitting surface code patches:

### Logical CNOT

```
┌─────────┐     ┌─────────┐
│ Logical  │─────│ Logical  │
│ Qubit A  │merge│ Qubit B  │    → Logical CNOT(A, B)
│ (d=23)   │─────│ (d=23)   │
└─────────┘     └─────────┘
```

Steps:
1. Merge X-boundaries of patches A and B (d rounds)
2. Measure merged stabilizers
3. Split patches (d rounds)
4. Apply corrections based on measurement outcomes

**Time:** 2d = 46 code cycles ≈ 46 μs (at 1 μs per cycle)

### Logical Toffoli (via Magic State Injection)

```
|ψ⟩ ──[T†]── = consume one T-state via gate teleportation

Toffoli = 7 T-gates:
  1. Prepare/consume 7 T-states (from distillation factories)
  2. 8 Clifford gates (lattice surgery CNOT)
  3. Classically-conditioned corrections

Time: ~7 × 46 = 322 code cycles ≈ 322 μs per Toffoli
```

Actually, with parallel T-state consumption and pipelining:

**Optimized Toffoli time:** ~4d = 92 code cycles ≈ 92 μs

## 10.4 Total Runtime

### Conservative Estimate

```
Total Toffoli-equivalent operations: 79M gates
Average gate time: ~50 μs (mix of CNOT and Toffoli)
Serial fraction: 3.1M depth levels

Runtime = 3.1M × 50 μs = 155 seconds ≈ 2.6 minutes
```

### Optimistic Estimate (with pipelining)

```
Depth: 3.1M
Time per depth level: 23 μs (d code cycles for one round)
Parallelism: gates at same depth execute simultaneously

Runtime = 3.1M × 23 μs = 71 seconds ≈ 1.2 minutes
```

### Per-Run Summary

| Metric | Conservative | Optimistic |
|---|---|---|
| Runtime per run | 155 s | 71 s |
| Number of runs | 2-3 | 2-3 |
| Total time to recover key | ~7 min | ~3 min |

## 10.5 Error Budget

The total computation must succeed with probability > 50% (can retry). The error budget:

```
Total gates: 79 × 10⁶
Logical error rate per gate: 10⁻¹⁰
Expected logical errors: 79 × 10⁶ × 10⁻¹⁰ = 7.9 × 10⁻³

Probability of zero errors: e^{-0.0079} ≈ 99.2%
```

This is excellent — the circuit succeeds with >99% probability per run.

### Error Budget Allocation

| Component | Gates | Error Contribution | % |
|---|---|---|---|
| Scalar multiplication | 74.2M | 7.42 × 10⁻³ | 94% |
| QFT | 0.13M | 1.3 × 10⁻⁵ | 0.2% |
| Checkpoint management | 4.0M | 4.0 × 10⁻⁴ | 5% |
| Other | 0.7M | 7.0 × 10⁻⁵ | 0.8% |
| **Total** | **79M** | **7.9 × 10⁻³** | **100%** |

## 10.6 Physical Qubit Technology Requirements

For the surface code to function at d=23 with p_phys = 10⁻³:

| Requirement | Value |
|---|---|
| Qubit count | ~7.7 million |
| Gate fidelity (2-qubit) | 99.9% |
| Gate fidelity (1-qubit) | 99.9% |
| Measurement fidelity | 99.9% |
| Qubit connectivity | 2D nearest-neighbor (grid) |
| Coherence time | > 100 μs (for 1 μs gate time) |
| Gate speed | ~100 ns (physical) |
| Syndrome extraction | ~1 μs per round |

Current state-of-the-art (2026):
- Best superconducting qubit chips: ~1,000 qubits, p_phys ≈ 3 × 10⁻³
- Path to 7.7M qubits: requires ~7,700× scale-up in qubit count

## 10.7 Alternative Error Correction Approaches

### Color Codes
- Higher transversal gate support (can do T-gates without distillation in some variants)
- Higher qubit overhead per logical qubit
- Better for circuits dominated by T-gates

### Quantum LDPC Codes
- Logarithmic overhead: O(n/log n) physical per logical
- Non-local connectivity required
- Could reduce physical qubit count to ~500K
- Still in early development

### Concatenated Codes
- Worse threshold (~10⁻⁴) but simpler decoders
- Not competitive for this application

**Our choice of surface codes** is based on their maturity, 2D layout compatibility, and well-understood performance characteristics.
