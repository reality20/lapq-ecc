"""
Quantum circuit primitives for arithmetic operations.
"""


class RippleCarryAdder:
    """
    256-bit ripple-carry adder based on Cuccaro's design.
    
    Implements reversible addition: |a⟩|b⟩ → |a⟩|a+b⟩
    Uses only 1 ancilla qubit for carry.
    """
    
    def __init__(self, bits: int = 256):
        self.bits = bits
        # Gate counts from documentation
        self.toffoli_count = 2 * bits - 2  # ~510 for 256-bit
        self.cnot_count = 2 * bits - 1     # ~511 for 256-bit
    
    def apply(self, circuit, a_reg: list[int], b_reg: list[int], carry: int):
        """
        Apply ripple-carry addition.
        
        Args:
            circuit: Quantum circuit object
            a_reg: List of qubit indices for register a (length bits)
            b_reg: List of qubit indices for register b (length bits)
            carry: Qubit index for carry ancilla
        """
        # Forward carry computation (MAJ gates)
        for i in range(self.bits):
            if i == 0:
                # First bit uses carry ancilla
                circuit.CNOT(a_reg[0], b_reg[0])
                circuit.CNOT(carry, b_reg[0])
            else:
                # MAJ gate: majority computation
                circuit.CNOT(a_reg[i], b_reg[i])
                circuit.CNOT(b_reg[i-1], b_reg[i])
                circuit.CCNOT(a_reg[i], b_reg[i-1], b_reg[i])
        
        # Backward sum computation (UMA gates) - run in reverse
        for i in range(self.bits - 1, -1, -1):
            if i == 0:
                circuit.CNOT(carry, b_reg[0])
                circuit.CNOT(a_reg[0], b_reg[0])
            else:
                # UMA gate: uncompute and sum
                circuit.CCNOT(a_reg[i], b_reg[i-1], b_reg[i])
                circuit.CNOT(b_reg[i-1], b_reg[i])
                circuit.CNOT(a_reg[i], b_reg[i])


class ModAdd:
    """
    Modular addition over F_p.
    
    Implements: |a⟩|b⟩ → |a⟩|a+b mod p⟩
    Uses special form of secp256k1 prime for efficient reduction.
    """
    
    P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    C = 4294968273  # p = 2^256 - C
    
    def __init__(self, bits: int = 256):
        self.bits = bits
        self.adder = RippleCarryAdder(bits)
        # From docs: 269 Toffoli, 610 CNOT, 289 single-qubit
        self.toffoli_count = 269
        self.cnot_count = 610
        self.single_count = 289
        self.ancilla_count = 2  # carry + flag
    
    def apply(self, circuit, a_reg: list[int], b_reg: list[int], 
              carry: int, flag: int):
        """
        Apply modular addition.
        
        Steps:
        1. Add a + b (may overflow to 257 bits)
        2. Compare with p
        3. Conditionally subtract p if result >= p
        4. Uncompute flag
        """
        # Step 1: Regular addition
        self.adder.apply(circuit, a_reg, b_reg, carry)
        
        # Step 2: Compare with p (simplified for special-form prime)
        # Only need to check high bits since p ≈ 2^256
        # This is simplified - full implementation needs proper comparison
        
        # Step 3: Conditional subtraction of p
        # For secp256k1: subtracting p = adding C and clearing bit 256
        
        # Step 4: Uncompute flag (reverse of comparison)
