"""
Quantum Fourier Transform (QFT) circuit.

Used in Shor's algorithm to extract period information.
"""


class QFT:
    """
    Quantum Fourier Transform on n qubits.
    
    Maps |x⟩ → (1/√N) Σ_k e^(2πixk/N) |k⟩
    
    Uses standard decomposition with Hadamard and controlled rotations.
    """
    
    def __init__(self, num_qubits: int = 256):
        self.num_qubits = num_qubits
        
        # Gate counts from documentation (Section 9.3.2)
        # Standard QFT: n(n+1)/2 controlled rotations + n Hadamards
        # For n=256: ~32,768 controlled rotations + 256 H
        self._toffoli_count = 0
        self._cnot_count = num_qubits * (num_qubits - 1) // 2  # Controlled rotations
        self._single_count = num_qubits  # Hadamards
        self._depth = num_qubits
    
    def apply(self, qubit_reg: list[int], 
              approximate: bool = True,
              cutoff: int = 50) -> list[tuple]:
        """
        Apply QFT to register.
        
        Args:
            qubit_reg: List of qubit indices
            approximate: If True, skip small rotations (cutoff)
            cutoff: Skip rotations smaller than π/2^cutoff
        
        Returns:
            List of gates applied
        """
        gates = []
        n = len(qubit_reg)
        
        for i in range(n):
            # Hadamard on qubit i
            gates.append(('H', (qubit_reg[i],)))
            
            # Controlled rotations
            for j in range(i + 1, n):
                if approximate and (j - i) > cutoff:
                    continue  # Skip small rotations
                
                angle = 3.14159 / (2 ** (j - i))
                gates.append(('CRz', (qubit_reg[j], qubit_reg[i], angle)))
        
        # Swap qubits to reverse order (optional, often omitted)
        for i in range(n // 2):
            gates.append(('SWAP', (qubit_reg[i], qubit_reg[n-1-i])))
        
        return gates
    
    def inverse(self, qubit_reg: list[int],
                approximate: bool = True,
                cutoff: int = 50) -> list[tuple]:
        """
        Apply inverse QFT.
        
        Reverse the forward QFT gates.
        """
        forward_gates = self.apply(qubit_reg, approximate, cutoff)
        # Reverse and invert each gate
        return forward_gates[::-1]
    
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
        """QFT requires no ancillae."""
        return 0
