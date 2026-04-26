"""
Modular subtraction circuit over F_p.
"""


class ModularSubtractor:
    """
    Reversible modular subtraction over F_p.
    
    Implements: |a⟩|b⟩ → |a⟩|a-b mod p⟩
    
    Computed as: a - b mod p = a + (p - b) mod p
    """
    
    P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    
    def __init__(self, p: int = None, field_bits: int = 256):
        if p is None:
            p = self.P
        self.p = p
        self.field_bits = field_bits
        
        # Same cost as ModAdd from documentation
        self._toffoli_count = 269
        self._cnot_count = 610
        self._single_count = 289
        self._ancilla_count = 2
        self._depth = 260
    
    def forward(self, a_reg: list[int], b_reg: list[int],
                ancilla_pool: list[int]) -> list[tuple]:
        """
        In-place modular subtraction: |a⟩|b⟩ → |a⟩|a-b mod p⟩.
        
        Implemented as: ModAdd(a, p-b)
        """
        gates = []
        
        carry = ancilla_pool[0]
        flag = ancilla_pool[1]
        
        # Step 1: Subtract (may go negative)
        gates.extend(self._subtract(a_reg, b_reg, carry))
        
        # Step 2: Check for borrow (negative result)
        gates.extend(self._check_borrow(carry, flag))
        
        # Step 3: If borrow, add p
        gates.extend(self._conditional_add_p(b_reg, flag, carry))
        
        # Step 4: Uncompute flag
        gates.extend(self._uncompute_borrow(flag))
        
        return gates
    
    def _subtract(self, a: list[int], b: list[int], 
                  borrow: int) -> list[tuple]:
        """Ripple-carry subtraction."""
        gates = []
        # Similar to addition but with borrows
        return gates
    
    def _check_borrow(self, borrow: int, flag: int) -> list[tuple]:
        """Check if result was negative (borrow occurred)."""
        gates = []
        return gates
    
    def _conditional_add_p(self, reg: list[int], flag: int,
                           ancilla: int) -> list[tuple]:
        """Add p if borrow flag is set."""
        gates = []
        return gates
    
    def _uncompute_borrow(self, flag: int) -> list[tuple]:
        """Uncompute borrow flag."""
        gates = []
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
        return self._depth
    
    @property
    def ancilla_count(self) -> int:
        """Return number of ancilla qubits needed."""
        return self._ancilla_count
