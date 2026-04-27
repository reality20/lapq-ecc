# Quantum ECDLP Solver for secp256k1 - Documentation Index

[![Back to Main README](../README.md)](../README.md)

## 📖 Project Overview

This documentation describes the full design and implementation of a **mathematically correct quantum solver** for the **Elliptic Curve Discrete Logarithm Problem (ECDLP)** on the **secp256k1** curve — the elliptic curve used in Bitcoin and Ethereum digital signatures.

The design implements Shor's algorithm with windowed arithmetic, targeting:

| Parameter | Value |
|-----------|-------|
| **Logical qubits** | ~6,004 error-corrected |
| **Gate count** | ~79 × 10⁶ (T + Clifford) |
| **Circuit depth** | ~3.1 × 10⁶ |
| **Curve** | secp256k1 (256-bit prime field) |
| **Algorithm** | Shor's algorithm with Jacobian coordinates |
| **Window size** | w=4 (combined addressing) |

## 📚 Document Index

### Foundations & Theory

| # | Document | Description |
|---|----------|-------------|
| 01 | [Mathematical Foundations](01_mathematical_foundations.md) | secp256k1 parameters, ECDLP definition, group theory, Shor's algorithm fundamentals |
| 12 | [Correctness Argument](12_correctness_argument.md) | Mathematical proof sketch of algorithm correctness |
| 15 | [Glossary & References](15_glossary_references.md) | Terminology, notation, and comprehensive bibliography |

### Architecture & Design

| # | Document | Description |
|---|----------|-------------|
| 02 | [Architecture Overview](02_architecture_overview.md) | End-to-end circuit architecture, qubit layout, execution pipeline |
| 08 | [Qubit Budget & Layout](08_qubit_budget.md) | Detailed allocation of all ~6,000 logical qubits |
| 13 | [Implementation Roadmap](13_implementation_roadmap.md) | Development phases, testing strategy, simulation approach |

### Quantum Arithmetic

| # | Document | Description |
|---|----------|-------------|
| 03 | [Finite Field Arithmetic](03_finite_field_arithmetic.md) | Modular addition, subtraction, multiplication, inversion over F_p |
| 04 | [Elliptic Curve Point Operations](04_ec_point_operations.md) | Point addition, doubling in Jacobian projective coordinates |
| 06 | [Windowed Arithmetic Optimization](06_windowed_arithmetic.md) | Window-based scalar multiplication to reduce gate count |
| 07 | [Reversible Computation & Uncomputation](07_reversible_computation.md) | Bennett's method, garbage-free modular arithmetic |

### Algorithm Implementation

| # | Document | Description |
|---|----------|-------------|
| 05 | [Shor's Algorithm Circuit](05_shors_algorithm_circuit.md) | Quantum phase estimation, controlled scalar multiplication, measurement |
| 09 | [Gate Count Analysis](09_gate_count_analysis.md) | Detailed breakdown of ~79M gates across all sub-circuits |
| 11 | [Classical Pre/Post Processing](11_classical_processing.md) | QROM table generation, lattice reduction, continued fractions, key recovery |

### Error Correction & Resources

| # | Document | Description |
|---|----------|-------------|
| 10 | [Quantum Error Correction](10_error_correction.md) | Surface code parameters, logical qubit encoding, physical qubit mapping |

### Reference

| # | Document | Description |
|---|----------|-------------|
| 14 | [API Reference](14_api_reference.md) | Complete module-level API documentation for the quantum circuit library |

## 🗂️ Directory Structure

```
docs/
├── 00_README.md                    ← You are here (Documentation Index)
├── 01_mathematical_foundations.md  ← Theory & background
├── 02_architecture_overview.md     ← System architecture
├── 03_finite_field_arithmetic.md   ← F_p operations
├── 04_ec_point_operations.md       ← Elliptic curve arithmetic
├── 05_shors_algorithm_circuit.md   ← Full Shor's algorithm
├── 06_windowed_arithmetic.md       ← Optimization techniques
├── 07_reversible_computation.md    ← Reversibility & uncomputation
├── 08_qubit_budget.md              ← Qubit allocation
├── 09_gate_count_analysis.md       ← Gate complexity analysis
├── 10_error_correction.md          ← Surface code estimates
├── 11_classical_processing.md      ← Classical algorithms
├── 12_correctness_argument.md      ← Correctness proof
├── 13_implementation_roadmap.md    ← Development plan
├── 14_api_reference.md             ← API documentation
└── 15_glossary_references.md       ← Glossary & bibliography
```

## 🔑 Key Design Decisions

1. **Jacobian (Projective) Coordinates**: Avoids quantum modular inversion during point addition (inversion costs ~100× more than multiplication)

2. **Windowed Scalar Multiplication**: Uses window size w=4 with combined addressing to reduce point additions from 256 to ~64 + precomputation via QROM

3. **Coset Representation of F_p**: Enables carry-free addition using specialized encoding

4. **Bennett's Uncomputation**: Achieves reversibility with only logarithmic ancilla overhead

5. **Surface Code Error Correction**: Code distance d=23 for target logical error rate ≤ 10⁻¹⁰ per gate

6. **Special-Form Modular Reduction**: Exploits p = 2²⁵⁶ - 4294968273 for efficient reduction

## 📊 Resource Summary

### Logical Resources
| Resource | Count | Notes |
|----------|-------|-------|
| Logical qubits | 6,004 | Data + ancillae |
| Toffoli gates | ~46.2 × 10⁶ | Dominant gate type |
| CNOT gates | ~24.8 × 10⁶ | Two-qubit Clifford |
| Single-qubit Clifford | ~8.0 × 10⁶ | H, S, etc. |
| **Total gates** | **~79.0 × 10⁶** | T + Clifford |
| Circuit depth | ~3.1 × 10⁶ | Critical path |

### Physical Resource Estimates (Surface Code)
| Resource | Estimate | Assumptions |
|----------|----------|-------------|
| Code distance | d = 23 | Physical error rate 10⁻³ |
| Physical qubits per logical | 1,058 | 2d² including routing |
| Total physical qubits | ~7.7 × 10⁶ | Including magic state factories |
| T-gates (decomposed) | ~323.4 × 10⁶ | From Toffoli decomposition |
| Estimated runtime | ~155 seconds | At 1 MHz cycle time |

## 🎯 Reading Guide

### For First-Time Readers
Start with these documents in order:
1. [Mathematical Foundations](01_mathematical_foundations.md) - Understand the problem
2. [Architecture Overview](02_architecture_overview.md) - See the big picture
3. [Shor's Algorithm Circuit](05_shors_algorithm_circuit.md) - Learn the core algorithm
4. [Resource Summary](#-resource-summary) - Understand the costs

### For Implementers
Focus on:
1. [API Reference](14_api_reference.md) - Module interfaces
2. [Finite Field Arithmetic](03_finite_field_arithmetic.md) - Building blocks
3. [EC Point Operations](04_ec_point_operations.md) - Core operations
4. [Implementation Roadmap](13_implementation_roadmap.md) - Development plan

### For Researchers
Deep dive into:
1. [Correctness Argument](12_correctness_argument.md) - Formal guarantees
2. [Gate Count Analysis](09_gate_count_analysis.md) - Complexity details
3. [Error Correction](10_error_correction.md) - Fault tolerance
4. [Glossary & References](15_glossary_references.md) - Background literature

## 🔗 Related Links

- [Main README](../README.md) - Project overview and quick start
- [GitHub Repository](https://github.com/ecdlp-solver/ecdlp-solver) - Source code
- [Issue Tracker](https://github.com/ecdlp-solver/ecdlp-solver/issues) - Bug reports and feature requests

## ⚠️ Disclaimer

This documentation is for **research and educational purposes only**. The described system targets a cryptographic primitive that secures real-world financial systems (Bitcoin, Ethereum). 

**No working quantum computer currently exists at the scale required to execute this algorithm.** Current estimates suggest fault-tolerant quantum computers with millions of physical qubits are needed.

Responsible disclosure and ethical considerations apply. Do not use for malicious purposes.

## 📄 License

MIT License - see the main [README](../README.md) for details.
