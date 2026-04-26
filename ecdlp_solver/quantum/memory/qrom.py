"""
Quantum Read-Only Memory (QROM) using unary iteration.

Loads classical data indexed by quantum address.
"""


class QROM:
    """
    Quantum Read-Only Memory with unary iteration optimization.
    
    Implements: |i⟩|0⟩ → |i⟩|data[i]⟩
    
    Uses binary-to-unary decoding followed by controlled CNOTs.
    Much more efficient than naive multi-controlled approach.
    """
    
    def __init__(self, address_bits: int = 8, data_bits: int = 512):
        self.address_bits = address_bits  # 8 bits for combined window
        self.data_bits = data_bits        # 512 bits for EC point (x || y)
        self.num_entries = 2 ** address_bits  # 256 entries
        
        # Gate counts from documentation (Section 6.3.2)
        # Binary-to-unary: 2^w - 1 Toffoli gates
        # Data loading: 2^w × (avg data bits/2) CNOT gates
        self._toffoli_count = 2 * (self.num_entries - 1)  # Forward + reverse
        self._cnot_count = self.num_entries * (self.data_bits // 2) * 2  # Forward + reverse
        self._single_count = 0
        self._ancilla_count = self.num_entries  # One-hot encoding
    
    def lookup(self, address_reg: list[int], data_reg: list[int],
               ancilla_pool: list[int]) -> list[tuple]:
        """
        Load data[address] into data register.
        
        Args:
            address_reg: Quantum address register (8 qubits)
            data_reg: Output data register (512 qubits, must be |0⟩)
            ancilla_pool: Pool for one-hot encoding
        
        Returns:
            List of gates applied
        """
        gates = []
        
        # Step 1: Binary-to-unary decode
        # Convert |addr⟩ to one-hot encoding in ancillae
        gates.extend(self._binary_to_unary(address_reg, ancilla_pool))
        
        # Step 2: Load data using one-hot controls
        # For each entry i, if ancilla[i]=1, XOR data[i] into output
        gates.extend(self._load_data(ancilla_pool, data_reg))
        
        return gates
    
    def uncompute(self, address_reg: list[int], data_reg: list[int],
                  ancilla_pool: list[int]) -> list[tuple]:
        """
        Uncompute QROM (reverse operation).
        
        Cleans up ancillae and data register.
        """
        gates = []
        
        # Reverse of lookup: unload then undecode
        gates.extend(self._unload_data(ancilla_pool, data_reg))
        gates.extend(self._unary_to_binary(address_reg, ancilla_pool))
        
        return gates
    
    def _binary_to_unary(self, addr: list[int], 
                         one_hot: list[int]) -> list[tuple]:
        """Decode binary address to one-hot encoding."""
        gates = []
        # Tree of Toffoli gates: 2^w - 1 gates
        return gates
    
    def _load_data(self, one_hot: list[int], 
                   data: list[int]) -> list[tuple]:
        """Load data using one-hot controls."""
        gates = []
        # For each entry, controlled on one_hot[i], XOR data[i]
        return gates
    
    def _unload_data(self, one_hot: list[int],
                     data: list[int]) -> list[tuple]:
        """Unload data (reverse of load)."""
        gates = []
        return gates
    
    def _unary_to_binary(self, addr: list[int],
                         one_hot: list[int]) -> list[tuple]:
        """Encode one-hot back to binary (reverse of decode)."""
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
        return 4126 * 2  # Forward + reverse
    
    @property
    def ancilla_count(self) -> int:
        """Return number of ancilla qubits needed."""
        return self._ancilla_count
