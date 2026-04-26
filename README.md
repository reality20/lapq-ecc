# lapq-ecc

Quantum ECDLP Solver for secp256k1 using Shor's algorithm with windowed arithmetic.

## Installation

Install from PyPI:

```bash
pip install ecdlp-solver
```

Or install from source:

```bash
pip install .
```

For development:

```bash
pip install -e ".[dev]"
```

## Features

- Full implementation of Shor's algorithm for ECDLP on secp256k1
- Windowed arithmetic with w=4 for optimized gate count
- ~6,000 logical qubits required
- ~79 × 10⁶ gates (T + Clifford)
- Complete classical pre/post-processing
- Quantum circuit components: adders, multipliers, QROM, QFT
- EC operations: point doubling, mixed addition, controlled addition
- Verification tools: gate counter, qubit tracker, depth analyzer
- Surface code error correction estimates

## Usage

```python
from ecdlp_solver import ECDLPSolver

# Create solver instance
solver = ECDLPSolver()

# Run the solver
result = solver.solve()
```

## License

MIT