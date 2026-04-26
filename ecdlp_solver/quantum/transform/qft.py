"""
Quantum Fourier Transform (QFT) circuit.

Used in Shor's algorithm to extract period information.
"""

import math
from typing import List, Tuple, Any


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
    
    def apply(self, circuit, qubit_reg: List[int], 
              approximate: bool = True,
              cutoff: int = 50) -> List[Tuple[str, List[int], List[Any]]]:
        """
        Apply QFT to register.
        
        The QFT circuit consists of:
        1. For each qubit i: Hadamard on i, then controlled rotations CRz(j,i) for j > i
        2. Final SWAP network to reverse qubit order
        
        Parameters
        ----------
        circuit : QuantumCircuit
            Circuit to apply gates to
        qubit_reg : List[int]
            List of qubit indices
        approximate : bool
            If True, skip small rotations (cutoff)
        cutoff : int
            Skip rotations smaller than π/2^cutoff
        
        Returns
        -------
        List of gates applied
        """
        gates = []
        n = len(qubit_reg)
        
        for i in range(n):
            # Hadamard on qubit i
            circuit.H(qubit_reg[i])
            
            # Controlled rotations
            for j in range(i + 1, n):
                if approximate and (j - i) > cutoff:
                    continue  # Skip small rotations
                
                # Use exact pi value
                angle = math.pi / (2 ** (j - i))
                circuit.CRz(qubit_reg[j], qubit_reg[i], angle)
        
        # Swap qubits to reverse order (needed for correct output ordering)
        for i in range(n // 2):
            circuit.SWAP(qubit_reg[i], qubit_reg[n-1-i])
        
        return circuit.gates
    
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
