"""
Oracle for Shor's ECDLP algorithm.

Computes |a⟩|b⟩|0⟩ → |a⟩|b⟩|aP + bQ⟩
"""


class Oracle:
    """
    Quantum oracle for ECDLP.
    
    Implements the function f(a, b) = aP + bQ as a reversible quantum operation.
    This is the core of Shor's algorithm for elliptic curves.
    """
    
    def __init__(self, P_affine: tuple, Q_affine: tuple,
                 window_size: int = 4):
        """
        Initialize oracle with classical points P and Q.
        
        Args:
            P_affine: Generator point (x, y) - classical constant
            Q_affine: Target public key (x, y) - classical constant
            window_size: Window size for optimization (default 4)
        """
        self.P = P_affine
        self.Q = Q_affine
        self.window_size = window_size
        
        # The oracle uses windowed scalar multiplication internally
        from .scalar_mult import WindowedScalarMult
        self.scalar_mult = WindowedScalarMult(window_size)
    
    def apply(self, a_reg: list[int], b_reg: list[int],
              x_out: list[int], y_out: list[int], z_out: list[int],
              ancilla_pool: list[int]) -> list[tuple]:
        """
        Apply oracle: compute aP + bQ.
        
        Args:
            a_reg: Quantum register for scalar a (256 qubits)
            b_reg: Quantum register for scalar b (256 qubits)
            x_out: Output X coordinate (Jacobian)
            y_out: Output Y coordinate
            z_out: Output Z coordinate
            ancilla_pool: Pool for workspace
        
        Returns:
            List of gates applied
        """
        return self.scalar_mult.multiply(
            a_reg, b_reg, x_out, y_out, z_out, ancilla_pool
        )
    
    def uncompute(self, a_reg: list[int], b_reg: list[int],
                  x_out: list[int], y_out: list[int], z_out: list[int],
                  ancilla_pool: list[int]) -> list[tuple]:
        """
        Uncompute oracle (reverse operation).
        
        Cleans up the output register.
        """
        forward_gates = self.apply(a_reg, b_reg, x_out, y_out, z_out, ancilla_pool)
        return forward_gates[::-1]
    
    @property
    def gate_count(self) -> dict:
        """Return gate count breakdown."""
        return self.scalar_mult.gate_count
    
    @property
    def depth(self) -> int:
        """Return circuit depth."""
        return self.scalar_mult.depth
    
    @property
    def ancilla_count(self) -> int:
        """Return number of ancilla qubits needed."""
        return self.scalar_mult.ancilla_count
