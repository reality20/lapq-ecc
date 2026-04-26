"""
Complete ECDLP Solver using Shor's algorithm.

This is the top-level interface that combines all components.
"""

from typing import Optional, Tuple
from .oracle import Oracle
from ..transform.qft import QFT


class ECDLPSolver:
    """
    Complete quantum ECDLP solver for secp256k1.
    
    Implements Shor's algorithm with windowed arithmetic optimization.
    
    Circuit structure:
        1. Initialize |0⟩^512 |0⟩^768 |ancillae⟩
        2. Apply Hadamards to input registers (a, b)
        3. Oracle: compute |a⟩|b⟩|aP + bQ⟩
        4. QFT on input registers
        5. Measure → (c, d)
        6. Classical post-processing: k = -d·c⁻¹ mod n
    
    Resource estimates (from documentation):
        - Logical qubits: ~6,004
        - Total gates: ~79 × 10⁶
        - Circuit depth: ~3.1 × 10⁶
        - Runtime (with error correction): ~1-3 minutes per run
    """
    
    def __init__(self, P: Tuple[int, int], Q: Tuple[int, int],
                 window_size: int = 4, field_bits: int = 256):
        """
        Initialize solver with curve points.
        
        Args:
            P: Generator point G (x, y)
            Q: Target public key (x, y)
            window_size: Window size for optimization (default 4)
            field_bits: Field bit width (default 256)
        """
        self.P = P
        self.Q = Q
        self.window_size = window_size
        self.field_bits = field_bits
        
        # Register sizes
        self.scalar_bits = field_bits  # 256 bits each for a and b
        self.point_bits = 3 * field_bits  # 768 bits for Jacobian point
        
        # Initialize components
        self.oracle = Oracle(P, Q, window_size)
        self.qft = QFT(field_bits)
        
        # Precomputed tables will be set later
        self.tables = None
    
    def generate_qrom_tables(self):
        """Generate precomputed point tables for QROM."""
        from ...classical.tables import generate_qrom_tables
        from ...classical.curve import ECPoint
        
        P_pt = ECPoint(self.P[0], self.P[1])
        Q_pt = ECPoint(self.Q[0], self.Q[1])
        
        self.tables = generate_qrom_tables(
            P_pt, Q_pt, self.window_size, self.field_bits
        )
        self.oracle.scalar_mult.set_tables(self.tables)
        
        return self.tables
    
    def build_circuit(self) -> dict:
        """
        Build the complete quantum circuit.
        
        Returns:
            Dictionary with circuit description and metadata
        """
        if self.tables is None:
            self.generate_qrom_tables()
        
        # Qubit allocation (from Chapter 8)
        total_qubits = 6004
        
        circuit = {
            'num_qubits': total_qubits,
            'registers': {
                'a': list(range(0, 256)),           # Scalar a
                'b': list(range(256, 512)),         # Scalar b
                'accumulator_X': list(range(512, 768)),   # X coordinate
                'accumulator_Y': list(range(768, 1024)),  # Y coordinate
                'accumulator_Z': list(range(1024, 1280)), # Z coordinate
                'qrom_output': list(range(1280, 1792)),   # QROM loaded point
                'qrom_ancilla': list(range(1792, 2056)),  # QROM one-hot
                'workspace': list(range(2056, 4096)),     # Arithmetic workspace
                'checkpoints': list(range(4096, 5632)),   # Checkpoint storage
                'flags': list(range(5632, 5680)),         # Control flags
                'padding': list(range(5680, 6004)),       # Alignment
            },
            'gates': [],
            'metadata': {
                'window_size': self.window_size,
                'field_bits': self.field_bits,
                'num_windows': self.field_bits // self.window_size,
            }
        }
        
        # Build gate sequence
        gates = []
        
        # Step 1: Hadamard initialization on input registers
        for i in range(512):
            gates.append(('H', (i,)))
        
        # Step 2: Oracle (windowed scalar multiplication)
        # This would expand to ~43M gates
        oracle_gates = self.oracle.apply(
            circuit['registers']['a'],
            circuit['registers']['b'],
            circuit['registers']['accumulator_X'],
            circuit['registers']['accumulator_Y'],
            circuit['registers']['accumulator_Z'],
            circuit['registers']['workspace'][:4724]
        )
        gates.extend(oracle_gates)
        
        # Step 3: QFT on input registers
        qft_a_gates = self.qft.apply(circuit['registers']['a'])
        qft_b_gates = self.qft.apply(circuit['registers']['b'])
        gates.extend(qft_a_gates)
        gates.extend(qft_b_gates)
        
        # Step 4: Measurement (classical output)
        measurement_regs = ['a', 'b']
        
        circuit['gates'] = gates
        circuit['measurement_registers'] = measurement_regs
        
        return circuit
    
    def get_resource_estimates(self) -> dict:
        """Return resource estimates from documentation."""
        return {
            'logical_qubits': 6004,
            'total_gates': 79000000,
            'toffoli_gates': 46200000,
            'cnot_gates': 24800000,
            'single_qubit_gates': 8000000,
            'circuit_depth': 3100000,
            't_gates': 323400000,  # For error correction
            'physical_qubits_surface_code': 7700000,
            'runtime_per_run_seconds': 71,  # Optimistic estimate
            'success_probability': 0.99,
        }
    
    def recover_key(self, c: int, d: int, n: Optional[int] = None) -> Optional[int]:
        """
        Recover private key from measurement results.
        
        Args:
            c: Measurement result from register a
            d: Measurement result from register b
            n: Group order (default: secp256k1 order)
        
        Returns:
            Private key k if successful, None otherwise
        """
        from ...classical.postprocess import recover_private_key
        from ...classical.curve import ECPoint, secp256k1_order
        
        if n is None:
            n = secp256k1_order()
        
        P = ECPoint(self.P[0], self.P[1])
        Q = ECPoint(self.Q[0], self.Q[1])
        
        return recover_private_key(c, d, n, P, Q)
