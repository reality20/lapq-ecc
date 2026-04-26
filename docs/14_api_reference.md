# 14 — API Reference

## 14.1 Module Hierarchy

```
ecdlp_solver/
├── classical/
│   ├── field.py              # F_p arithmetic
│   ├── curve.py              # EC point operations
│   ├── tables.py             # Precomputed table generation
│   └── postprocess.py        # Key recovery
├── quantum/
│   ├── primitives/
│   │   ├── adder.py          # Ripple-carry adder
│   │   ├── comparator.py     # Magnitude comparator
│   │   ├── multiplier.py     # Schoolbook & Karatsuba multiplier
│   │   └── cswap.py          # Controlled swap
│   ├── arithmetic/
│   │   ├── mod_add.py        # Modular addition
│   │   ├── mod_sub.py        # Modular subtraction
│   │   ├── mod_mul.py        # Modular multiplication (Montgomery)
│   │   ├── mod_reduce.py     # Special-form reduction
│   │   └── mod_negate.py     # Modular negation
│   ├── ec/
│   │   ├── point_double.py   # Jacobian point doubling
│   │   ├── point_add.py      # Mixed Jacobian-affine addition
│   │   ├── point_negate.py   # Point negation
│   │   ├── ctrl_point_add.py # Controlled point addition
│   │   └── special_cases.py  # Identity/equality/negation handling
│   ├── memory/
│   │   ├── qrom.py           # Quantum read-only memory
│   │   ├── qrom_uncompute.py # QROM reverse
│   │   └── checkpoint.py     # Pebble-game checkpointing
│   ├── transform/
│   │   ├── qft.py            # Quantum Fourier Transform
│   │   └── hadamard.py       # Parallel Hadamard layer
│   └── top/
│       ├── scalar_mult.py    # Windowed scalar multiplication
│       ├── oracle.py         # Full oracle circuit
│       └── ecdlp_solver.py   # Top-level solver
├── verification/
│   ├── gate_counter.py       # Gate count analysis
│   ├── qubit_counter.py      # Qubit allocation tracker
│   ├── depth_analyzer.py     # Circuit depth computation
│   └── correctness_test.py   # Functional verification
└── error_correction/
    ├── surface_code.py       # Surface code parameters
    ├── magic_state.py        # Distillation factory
    ├── lattice_surgery.py    # Logical gate scheduling
    └── physical_estimate.py  # Physical resource estimation
```

## 14.2 Core Quantum Circuit API

### 14.2.1 QuantumRegister

```python
class QuantumRegister:
    """A contiguous block of qubits."""

    def __init__(self, size: int, name: str = ""):
        """Allocate a register of `size` qubits, initialized to |0⟩."""

    def __getitem__(self, index) -> Qubit | QuantumRegister:
        """Access individual qubits or slices."""

    @property
    def size(self) -> int:
        """Number of qubits in this register."""
```

### 14.2.2 JacobianPointRegister

```python
class JacobianPointRegister:
    """Three field-element registers representing a Jacobian EC point."""

    def __init__(self, field_bits: int = 256):
        self.X = QuantumRegister(field_bits, "X")
        self.Y = QuantumRegister(field_bits, "Y")
        self.Z = QuantumRegister(field_bits, "Z")

    @property
    def total_qubits(self) -> int:
        return 3 * self.X.size  # 768
```

### 14.2.3 AncillaPool

```python
class AncillaPool:
    """Manages allocation and deallocation of ancilla qubits."""

    def __init__(self, total_ancillae: int):
        """Initialize pool with `total_ancillae` qubits in |0⟩ state."""

    def allocate(self, count: int) -> QuantumRegister:
        """Allocate `count` clean ancillae from the pool.
        Raises PoolExhaustedError if insufficient qubits available."""

    def release(self, register: QuantumRegister):
        """Return qubits to the pool. Caller must ensure they are in |0⟩ state."""

    @property
    def available(self) -> int:
        """Number of currently available ancillae."""

    @property
    def peak_usage(self) -> int:
        """Maximum simultaneous ancilla usage observed."""
```

## 14.3 Arithmetic Circuit API

### 14.3.1 ModularAdder

```python
class ModularAdder:
    """Reversible modular addition over F_p."""

    def __init__(self, p: int, field_bits: int = 256):
        """Configure for modulus p with field_bits-bit representation."""

    def forward(self, a: QuantumRegister, b: QuantumRegister,
                ancilla: AncillaPool) -> None:
        """In-place: |a⟩|b⟩ → |a⟩|a+b mod p⟩.

        Args:
            a: First operand (unchanged)
            b: Second operand (overwritten with sum)
            ancilla: Pool for temporary qubits (2 needed)
        """

    def inverse(self, a: QuantumRegister, b: QuantumRegister,
                ancilla: AncillaPool) -> None:
        """In-place: |a⟩|a+b mod p⟩ → |a⟩|b⟩. Reverse of forward."""

    @property
    def gate_count(self) -> dict:
        """Returns {'toffoli': 269, 'cnot': 610, 'single': 289}"""

    @property
    def depth(self) -> int:
        """Returns 260"""

    @property
    def ancilla_count(self) -> int:
        """Returns 2"""
```

### 14.3.2 ModularMultiplier

```python
class ModularMultiplier:
    """Reversible modular multiplication over F_p using Karatsuba + Montgomery."""

    def __init__(self, p: int, field_bits: int = 256,
                 method: str = "karatsuba_montgomery"):
        """Configure multiplier.

        Args:
            p: Field modulus
            field_bits: Bit width of field elements
            method: "schoolbook", "karatsuba", "karatsuba_montgomery"
        """

    def forward(self, a: QuantumRegister, b: QuantumRegister,
                output: QuantumRegister, ancilla: AncillaPool) -> None:
        """Out-of-place: |a⟩|b⟩|0⟩ → |a⟩|b⟩|a·b mod p⟩.

        Uses Bennett's trick internally (compute, copy, uncompute).

        Args:
            a: First operand (unchanged)
            b: Second operand (unchanged)
            output: Target register for result (must be |0⟩)
            ancilla: Pool for workspace (768 needed)
        """

    def forward_classical(self, a_classical: int, b: QuantumRegister,
                          output: QuantumRegister, ancilla: AncillaPool) -> None:
        """Multiply quantum register by classical constant.
        |b⟩|0⟩ → |b⟩|a·b mod p⟩ where a is classically known."""

    @property
    def gate_count(self) -> dict:
        """Returns {'toffoli': 58836, 'cnot': 68520, 'single': 0}"""
```

### 14.3.3 ModularReducer

```python
class ModularReducer:
    """Reduce a 512-bit value modulo p = 2^256 - c."""

    def __init__(self, p: int, c: int = 4294968273):
        """Configure for special-form modulus."""

    def forward(self, extended: QuantumRegister,
                output: QuantumRegister, ancilla: AncillaPool) -> None:
        """Reduce: |x⟩_512 |0⟩_256 → |x⟩_512 |x mod p⟩_256."""
```

## 14.4 EC Operations API

### 14.4.1 PointDoubler

```python
class PointDoubler:
    """Jacobian point doubling on y² = x³ + 7 (a=0)."""

    def __init__(self, p: int, field_bits: int = 256):
        """Configure for curve over F_p."""

    def forward(self, point: JacobianPointRegister,
                ancilla: AncillaPool) -> None:
        """In-place doubling: |(X:Y:Z)⟩ → |(X':Y':Z')⟩ = |2(X:Y:Z)⟩.

        Modifies point register in-place.
        Uses 7 ModMul + 4 ModAdd internally.
        """

    @property
    def gate_count(self) -> dict:
        """Returns {'toffoli': 345220, ...}"""
```

### 14.4.2 MixedPointAdder

```python
class MixedPointAdder:
    """Add a classical affine point to a quantum Jacobian point."""

    def __init__(self, p: int, field_bits: int = 256):
        """Configure for curve over F_p."""

    def forward(self, accum: JacobianPointRegister,
                x2: int, y2: int,
                ancilla: AncillaPool) -> None:
        """Mixed addition: |R⟩ → |R + (x2, y2)⟩.

        Args:
            accum: Jacobian accumulator point (modified in-place)
            x2, y2: Classical affine coordinates of the addend
            ancilla: Pool (1536 needed for temporaries)

        Special cases handled internally:
            - R = O (identity): result = (x2, y2)
            - (x2,y2) = O: result = R (no-op since classical identity not loaded)
            - R = (x2,y2): switches to doubling
            - R = -(x2,y2): result = O
        """

    @property
    def gate_count(self) -> dict:
        """Returns {'toffoli': 542117, ...}"""
```

## 14.5 QROM API

```python
class QROM:
    """Quantum Read-Only Memory using unary iteration."""

    def __init__(self, data: list[int], data_bits: int,
                 address_bits: int):
        """Configure QROM.

        Args:
            data: List of 2^address_bits classical data values
            data_bits: Bit width of each data entry (512 for EC points)
            address_bits: Bit width of address (8 for combined window)
        """

    def lookup(self, address: QuantumRegister,
               output: QuantumRegister, ancilla: AncillaPool) -> None:
        """Load data: |addr⟩|0⟩ → |addr⟩|data[addr]⟩."""

    def unlookup(self, address: QuantumRegister,
                 output: QuantumRegister, ancilla: AncillaPool) -> None:
        """Uncompute: |addr⟩|data[addr]⟩ → |addr⟩|0⟩."""

    @property
    def gate_count(self) -> dict:
        """Returns {'toffoli': 510, 'cnot': 65536, 'single': 0}"""
```

## 14.6 Top-Level Solver API

```python
class ECDLPSolver:
    """Complete quantum ECDLP solver for secp256k1."""

    def __init__(self, P: ECPoint, Q: ECPoint, n: int,
                 window_size: int = 4, num_checkpoints: int = 2):
        """Initialize solver.

        Args:
            P: Generator point
            Q: Target point (public key)
            n: Group order
            window_size: QROM window size (default 4, combined = 8)
            num_checkpoints: Pebble-game checkpoints (default 2)
        """

    def precompute_tables(self) -> list[dict]:
        """Generate QROM lookup tables. Returns 64 tables."""

    def build_circuit(self) -> QuantumCircuit:
        """Construct the full quantum circuit.

        Returns:
            QuantumCircuit with ~79M gates on ~6,004 qubits
        """

    def classical_postprocess(self, c: int, d: int) -> int | None:
        """Recover private key from measurement.

        Args:
            c, d: Measurement results from quantum registers a, b

        Returns:
            Private key k if verification succeeds, None otherwise
        """

    def solve(self, quantum_backend) -> int:
        """End-to-end solver.

        Args:
            quantum_backend: Quantum computer interface with .run(circuit) method

        Returns:
            Private key k

        Raises:
            ECDLPError: If key not recovered after max_retries attempts
        """

    def resource_summary(self) -> dict:
        """Return resource estimates.

        Returns:
            {
                'logical_qubits': 6004,
                'toffoli_gates': 46200000,
                'cnot_gates': 24800000,
                'single_qubit_gates': 8000000,
                'total_gates': 79000000,
                'circuit_depth': 3100000,
                't_gates': 323400000,
                'physical_qubits_estimate': 7700000,
                'estimated_runtime_seconds': 155,
            }
        """
```

## 14.7 Verification API

```python
class GateCounter:
    """Traverses a circuit and counts gates by type."""

    def count(self, circuit: QuantumCircuit) -> dict:
        """Returns gate counts: {'toffoli': N, 'cnot': M, 'single': K, 'total': T}"""

class QubitTracker:
    """Tracks qubit allocation throughout circuit execution."""

    def analyze(self, circuit: QuantumCircuit) -> dict:
        """Returns: {'total': N, 'peak': M, 'data': D, 'ancilla': A}"""

class DepthAnalyzer:
    """Computes circuit depth (critical path length)."""

    def analyze(self, circuit: QuantumCircuit) -> int:
        """Returns circuit depth."""

class CorrectnessVerifier:
    """Verifies circuit correctness by simulation on small instances."""

    def verify_modadd(self, p: int, bits: int) -> bool:
        """Exhaustively test ModAdd for all inputs in [0, p-1]²."""

    def verify_modmul(self, p: int, bits: int, samples: int = 1000) -> bool:
        """Test ModMul for random inputs."""

    def verify_point_add(self, curve, samples: int = 100) -> bool:
        """Test point addition against classical implementation."""

    def verify_full_algorithm(self, curve, known_key: int) -> bool:
        """End-to-end test: solve ECDLP for a known key on a small curve."""
```

## 14.8 Error Correction API

```python
class SurfaceCodeEstimator:
    """Estimate physical resources for surface code implementation."""

    def __init__(self, physical_error_rate: float = 1e-3,
                 target_logical_error_rate: float = 1e-10):
        """Configure error correction parameters."""

    def code_distance(self) -> int:
        """Compute required code distance. Returns 23."""

    def physical_qubits_per_logical(self) -> int:
        """Returns 2d² = 1058."""

    def total_physical_qubits(self, logical_qubits: int) -> int:
        """Returns total physical qubit count including routing and factories."""

    def magic_state_factories(self, t_gate_rate: float) -> int:
        """Compute number of distillation factories needed."""

    def runtime_estimate(self, circuit_depth: int) -> float:
        """Estimate runtime in seconds."""
```
