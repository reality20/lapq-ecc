# Quantum ECDLP Solver for secp256k1

## Project Overview

This project documents the full design and implementation of a **mathematically correct quantum solver** for the **Elliptic Curve Discrete Logarithm Problem (ECDLP)** on the **secp256k1** curve — the curve used in Bitcoin and Ethereum digital signatures.

The design targets:

| Parameter | Value |
|---|---|
| **Logical qubits** | ~6,000 error-corrected |
| **Gate count** | ~79 × 10⁶ (T + Clifford) |
| **Curve** | secp256k1 (256-bit prime field) |
| **Algorithm** | Shor's algorithm with windowed arithmetic |

## Document Index

| # | Document | Description |
|---|---|---|
| 01 | [Mathematical Foundations](01_mathematical_foundations.md) | secp256k1 parameters, ECDLP definition, Shor's algorithm theory |
| 02 | [Architecture Overview](02_architecture_overview.md) | End-to-end circuit architecture, qubit layout, pipeline |
| 03 | [Finite Field Arithmetic](03_finite_field_arithmetic.md) | Modular add, mul, inv over F_p for the secp256k1 prime |
| 04 | [Elliptic Curve Point Operations](04_ec_point_operations.md) | Point addition, doubling in projective coordinates |
| 05 | [Shor's Algorithm Circuit](05_shors_algorithm_circuit.md) | Quantum phase estimation, controlled scalar multiplication |
| 06 | [Windowed Arithmetic Optimization](06_windowed_arithmetic.md) | Window-based exponentiation to reduce gate count |
| 07 | [Reversible Computation & Uncomputation](07_reversible_computation.md) | Bennett's method, garbage-free modular arithmetic |
| 08 | [Qubit Budget & Layout](08_qubit_budget.md) | Detailed allocation of all ~6,000 logical qubits |
| 09 | [Gate Count Analysis](09_gate_count_analysis.md) | Breakdown of ~79M gates across sub-circuits |
| 10 | [Quantum Error Correction](10_error_correction.md) | Surface code, logical qubit encoding, physical qubit mapping |
| 11 | [Classical Pre/Post Processing](11_classical_processing.md) | Lattice reduction, continued fractions, key recovery |
| 12 | [Correctness Argument](12_correctness_argument.md) | Mathematical proof sketch of algorithm correctness |
| 13 | [Implementation Roadmap](13_implementation_roadmap.md) | Development phases, testing, simulation strategy |
| 14 | [API Reference](14_api_reference.md) | Module-level API for the quantum circuit library |
| 15 | [Glossary & References](15_glossary_references.md) | Terminology and bibliography |

## Quick Start

```
docs/
├── 00_README.md                    ← You are here
├── 01_mathematical_foundations.md
├── 02_architecture_overview.md
├── 03_finite_field_arithmetic.md
├── 04_ec_point_operations.md
├── 05_shors_algorithm_circuit.md
├── 06_windowed_arithmetic.md
├── 07_reversible_computation.md
├── 08_qubit_budget.md
├── 09_gate_count_analysis.md
├── 10_error_correction.md
├── 11_classical_processing.md
├── 12_correctness_argument.md
├── 13_implementation_roadmap.md
├── 14_api_reference.md
├── 15_glossary_references.md
└── figures/
    └── (ASCII circuit diagrams embedded in docs)
```

## Key Design Decisions

1. **Projective (Jacobian) coordinates** for elliptic curve arithmetic — avoids quantum modular inversion during point addition.
2. **Windowed scalar multiplication** with window size w=4 — reduces the number of quantum point additions from 256 to ~64 + precomputation.
3. **Coset representation** of F_p — enables carry-free addition.
4. **Bennett's uncomputation** for reversibility with logarithmic ancilla overhead.
5. **Surface code** error correction with code distance d=23 for target logical error rate ≤ 10⁻¹⁰ per gate.

## Resource Summary

| Resource | Count |
|---|---|
| Logical qubits | 6,004 |
| Toffoli gates | ~46.2 × 10⁶ |
| CNOT gates | ~24.8 × 10⁶ |
| Single-qubit Clifford gates | ~8.0 × 10⁶ |
| **Total gates** | **~79.0 × 10⁶** |
| Circuit depth | ~3.1 × 10⁶ |
| T-gate count (from Toffoli decomposition) | ~323.4 × 10⁶ |

## License & Disclaimer

This documentation is for **research and educational purposes only**. The described system targets a cryptographic primitive that secures real-world financial systems. Responsible disclosure and ethical considerations apply. No working quantum computer currently exists at the scale required to execute this algorithm.
