# lapq-ecc: Quantum ECDLP Solver for secp256k1

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A mathematically correct quantum solver for the **Elliptic Curve Discrete Logarithm Problem (ECDLP)** on the **secp256k1** curve using Shor's algorithm with windowed arithmetic.

## 📋 Overview

This package implements the full design for solving ECDLP on Bitcoin's secp256k1 curve, targeting:

| Parameter | Value |
|-----------|-------|
| **Logical Qubits** | ~6,004 error-corrected |
| **Gate Count** | ~79 × 10⁶ (T + Clifford) |
| **Circuit Depth** | ~3.1 × 10⁶ |
| **Window Size** | w=4 (combined addressing) |
| **Algorithm** | Shor's algorithm with Jacobian coordinates |

## 🚀 Installation

### From PyPI
```bash
pip install ecdlp-solver
```

### From Source
```bash
pip install .
```

### Development Mode
```bash
pip install -e ".[dev]"
```

## 🎯 Features

### Core Capabilities
- **Full Shor's Algorithm Implementation**: Complete quantum circuit for ECDLP on secp256k1
- **Windowed Arithmetic**: Optimized scalar multiplication with w=4 windows reducing operations from 256 to ~64
- **Jacobian Coordinates**: Projective coordinate system avoiding costly modular inversions
- **Reversible Computation**: Bennett's uncomputation method for garbage-free arithmetic

### Quantum Components
- **Primitives**: Ripple-carry adders, comparators, multipliers (schoolbook & Karatsuba), controlled swaps
- **Modular Arithmetic**: F_p addition, subtraction, multiplication, reduction for secp256k1 prime
- **EC Operations**: Point doubling, mixed addition, negation, controlled point addition
- **Memory Systems**: QROM with unary iteration, checkpoint-based pebble game
- **Transforms**: Quantum Fourier Transform (QFT) for phase estimation

### Classical Support
- **Field Arithmetic**: Efficient F_p operations for secp256k1 prime (p = 2²⁵⁶ - 4294968273)
- **Curve Operations**: ECPoint class with affine coordinate arithmetic
- **Pre/Post Processing**: QROM table generation, lattice reduction, continued fractions for key recovery

### Verification & Analysis
- **Gate Counter**: Detailed breakdown by gate type (Toffoli, CNOT, single-qubit)
- **Qubit Tracker**: Peak usage analysis and allocation tracking
- **Depth Analyzer**: Critical path computation
- **Error Correction**: Surface code estimates with code distance d=23

## 📖 Quick Start

### Basic Usage
```python
from ecdlp_solver import ECDLPSolver

# Create solver instance with generator P and target Q
P = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)
Q = (...)  # Your target public key

solver = ECDLPSolver(P=P, Q=Q, window_size=4)

# Build and execute the circuit
result = solver.solve(backend='qpu1')

if result['success']:
    print(f"Recovered private key: {hex(result['recovered_key'])}")
else:
    print(f"Solver failed: {result.get('error', 'Unknown error')}")
```

### Resource Estimation
```python
from ecdlp_solver import ECDLPSolver

solver = ECDLPSolver(P, Q)
resources = solver.resource_estimate

print(f"Total qubits: {resources['total_qubits']}")
print(f"Toffoli gates: {resources['toffoli_gates']:,}")
print(f"CNOT gates: {resources['cnot_gates']:,}")
print(f"Circuit depth: {resources['circuit_depth']:,}")
```

### Component-Level Access
```python
from ecdlp_solver import (
    Fp, ECPoint,                    # Classical types
    ModularAdder, ModularMultiplier, # Arithmetic circuits
    PointDoubler, MixedPointAdder,   # EC operations
    QROM, QFT,                       # Memory & transforms
    GateCounter, QubitTracker        # Verification tools
)

# Example: Modular addition
adder = ModularAdder(p=Fp.P, field_bits=256)
print(f"Adder uses {adder.ancilla_count} ancillae")
print(f"Gate count: {adder.gate_count}")
```

## 🏗️ Architecture

### Module Structure
```
ecdlp_solver/
├── classical/           # Classical pre/post-processing
│   ├── field.py         # F_p arithmetic
│   ├── curve.py         # EC point operations
│   ├── tables.py        # QROM table generation
│   └── postprocess.py   # Key recovery algorithms
├── quantum/             # Quantum circuit components
│   ├── primitives/      # Basic gates & circuits
│   ├── arithmetic/      # Modular arithmetic
│   ├── ec/              # Elliptic curve operations
│   ├── memory/          # QROM & checkpointing
│   ├── transform/       # QFT & Hadamard layers
│   └── top/             # Top-level solver assembly
├── verification/        # Analysis & testing tools
│   ├── gate_counter.py
│   ├── qubit_counter.py
│   └── depth_analyzer.py
└── error_correction/    # Surface code estimates
    └── surface_code.py
```

### Algorithm Flow
1. **Initialization**: Prepare superposition over coefficients (a, b) ∈ [0, n-1]²
2. **Oracle Application**: Compute |a⟩|b⟩ → |a⟩|b⟩|aP + bQ⟩ using windowed scalar multiplication
3. **Quantum Fourier Transform**: Apply QFT† to extract periodicity
4. **Measurement**: Collapse to obtain classical bits (c, d)
5. **Classical Post-processing**: Use continued fractions to recover private key k

## 📊 Resource Breakdown

### Qubit Allocation (~6,004 total)
| Register | Qubits | Purpose |
|----------|--------|---------|
| Address a | 256 | Superposition coefficient |
| Address b | 256 | Superposition coefficient |
| Accumulator X | 257 | Jacobian X coordinate |
| Accumulator Y | 257 | Jacobian Y coordinate |
| Accumulator Z | 257 | Jacobian Z coordinate |
| Ancillae | ~4,721 | Workspace for arithmetic |

### Gate Count (~79M total)
| Gate Type | Count | Percentage |
|-----------|-------|------------|
| Toffoli | ~46.2M | 58.5% |
| CNOT | ~24.8M | 31.4% |
| Single-qubit Clifford | ~8.0M | 10.1% |

### Error Correction Estimates
Assuming surface code with physical error rate 10⁻³:
- **Code Distance**: d = 23
- **Physical Qubits per Logical**: 2d² = 1,058
- **Total Physical Qubits**: ~7.7 × 10⁶ (including routing & factories)
- **Estimated Runtime**: ~155 seconds at 1 MHz cycle time

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [Mathematical Foundations](docs/01_mathematical_foundations.md) | secp256k1 parameters, ECDLP definition, Shor's theory |
| [Architecture Overview](docs/02_architecture_overview.md) | End-to-end circuit design and qubit layout |
| [Finite Field Arithmetic](docs/03_finite_field_arithmetic.md) | Modular operations over F_p |
| [EC Point Operations](docs/04_ec_point_operations.md) | Jacobian coordinate arithmetic |
| [Shor's Algorithm Circuit](docs/05_shors_algorithm_circuit.md) | Phase estimation and controlled operations |
| [Windowed Arithmetic](docs/06_windowed_arithmetic.md) | Optimization technique for reduced gate count |
| [Reversible Computation](docs/07_reversible_computation.md) | Uncomputation strategies |
| [Qubit Budget](docs/08_qubit_budget.md) | Detailed qubit allocation |
| [Gate Count Analysis](docs/09_gate_count_analysis.md) | Per-component gate breakdown |
| [Error Correction](docs/10_error_correction.md) | Surface code implementation |
| [Classical Processing](docs/11_classical_processing.md) | Pre/post-processing algorithms |
| [Correctness Argument](docs/12_correctness_argument.md) | Mathematical proof sketch |
| [Implementation Roadmap](docs/13_implementation_roadmap.md) | Development phases |
| [API Reference](docs/14_api_reference.md) | Complete module documentation |
| [Glossary](docs/15_glossary_references.md) | Terminology and bibliography |

## 🔬 Technical Details

### Key Design Decisions

1. **Jacobian Coordinates**: Avoids modular inversion during point addition (inversion costs ~100× multiplication)
2. **Combined Window Addressing**: Uses 8-bit address (two 4-bit windows) to halve QROM lookups
3. **Coset Representation**: Enables carry-free addition in F_p
4. **Bennett's Uncomputation**: Logarithmic ancilla overhead for reversible computation
5. **Special-Form Reduction**: Exploits p = 2²⁵⁶ - c for efficient modular reduction

### secp256k1 Parameters
```python
Prime:       p = 2^256 - 4294968273
           = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
Order:       n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Curve:       y² = x³ + 7 (over F_p)
Generator G: (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
              0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)
```

## 🧪 Testing

Run the test suite:
```bash
pytest test_phases_567.py -v
```

For coverage report:
```bash
pytest --cov=ecdlp_solver --cov-report=html
```

## ⚠️ Disclaimer

This software is for **research and educational purposes only**. The described system targets a cryptographic primitive that secures real-world financial systems (Bitcoin, Ethereum). 

**No working quantum computer currently exists at the scale required to execute this algorithm.** Current estimates suggest fault-tolerant quantum computers with millions of physical qubits are needed.

Responsible disclosure and ethical considerations apply. Do not use for malicious purposes.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines before submitting PRs.

## 📧 Contact

- Issues: [GitHub Issues](https://github.com/ecdlp-solver/ecdlp-solver/issues)
- Email: ecdlp-solver@example.com

## 🙏 Acknowledgments

This implementation builds upon foundational work in:
- Shor's algorithm (1994)
- Quantum arithmetic (Beauregard, 2002; Häner et al., 2016)
- Elliptic curve quantum algorithms (Proos & Zalka, 2003)
- Windowed optimization techniques (Roetteler et al., 2017)