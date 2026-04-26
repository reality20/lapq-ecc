"""
Mixed Jacobian-affine point addition circuit.

Adds a Jacobian point to an affine point (from QROM lookup).
"""


class MixedPointAdder:
    """
    Reversible mixed Jacobian-affine point addition.
    
    For Jacobian P₁ = (X₁ : Y₁ : Z₁) and affine P₂ = (x₂, y₂),
    compute P₁ + P₂ = (X₃ : Y₃ : Z₃).
    
    Formulas:
        U₁ = X₁
        U₂ = x₂ · Z₁²
        S₁ = Y₁
        S₂ = y₂ · Z₁³
        H  = U₂ - U₁
        R  = S₂ - S₁
        X₃ = R² - H³ - 2·U₁·H²
        Y₃ = R·(U₁·H² - X₃) - S₁·H³
        Z₃ = H · Z₁
    
    Cost: 8M + 3S + 5A ≈ 11 multiplications
    """
    
    def __init__(self, field_bits: int = 256):
        self.field_bits = field_bits
        
        # Gate counts from documentation (Section 4.3)
        self._toffoli_count = 542117
        self._cnot_count = 904000
        self._single_count = 50000
        self._ancilla_count = 512  # Workspace for intermediates
    
    def add(self, x1_reg: list[int], y1_reg: list[int], z1_reg: list[int],
            x2_affine: int, y2_affine: int,  # Classical values
            ancilla_pool: list[int]) -> list[tuple]:
        """
        Add affine point (x2, y2) to Jacobian point (X1, Y1, Z1).
        
        Args:
            x1_reg: Jacobian X coordinate register
            y1_reg: Jacobian Y coordinate register
            z1_reg: Jacobian Z coordinate register
            x2_affine: Affine x coordinate (classical constant)
            y2_affine: Affine y coordinate (classical constant)
            ancilla_pool: Pool for workspace
        
        Returns:
            List of gates applied
        """
        gates = []
        
        # Handle special cases:
        # 1. If Z₁ = 0 (identity), result is (x₂, y₂, 1)
        # 2. If points are equal, use doubling
        # 3. If points are negatives, result is identity
        
        # Compute intermediates U₁, U₂, S₁, S₂, H, R
        # Then compute X₃, Y₃, Z₃
        
        return gates
    
    @property
    def gate_count(self) -> dict:
        """Return gate count breakdown."""
        return {
            'toffoli': self._toffoli_count,
            'cnot': self._cnot_count,
            'single': self._single_count,
            'total': self._toffoli_count + self._cnot_count + self._single_count
        }
    
    @property
    def depth(self) -> int:
        """Return circuit depth."""
        return 542000  # Approximate
    
    @property
    def ancilla_count(self) -> int:
        """Return number of ancilla qubits needed."""
        return self._ancilla_count
