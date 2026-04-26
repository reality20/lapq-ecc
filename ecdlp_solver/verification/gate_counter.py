"""
Phase 7: Gate Counter for resource estimation.
Counts and categorizes all gates in a quantum circuit.
"""

from typing import Dict, List, Tuple


class GateCounter:
    """
    Comprehensive gate counter for quantum circuits.
    
    Tracks Toffoli, CNOT, single-qubit gates separately.
    Provides detailed breakdowns and totals.
    """
    
    def __init__(self):
        self.toffoli_count = 0
        self.cnot_count = 0
        self.single_count = 0
        self.other_count = 0
        self.gate_breakdown = {}
        
    def count(self, gates: List[Tuple]) -> Dict:
        """
        Count gates from a list of gate tuples.
        
        Args:
            gates: List of (gate_name, *qubits) tuples
            
        Returns:
            Dictionary with gate counts
        """
        self.toffoli_count = 0
        self.cnot_count = 0
        self.single_count = 0
        self.other_count = 0
        self.gate_breakdown = {}
        
        for gate in gates:
            gate_name = gate[0]
            
            if gate_name == 'CCNOT' or gate_name == 'Toffoli':
                self.toffoli_count += 1
            elif gate_name == 'CNOT':
                self.cnot_count += 1
            elif gate_name in ['H', 'X', 'Y', 'Z', 'S', 'T', 'RX', 'RY', 'RZ', 'CRz']:
                self.single_count += 1
            elif gate_name in ['SWAP', 'CSWAP']:
                # SWAP = 3 CNOT, CSWAP = 2 Toffoli + 1 CNOT (approx)
                if gate_name == 'SWAP':
                    self.cnot_count += 3
                else:
                    self.toffoli_count += 2
                    self.cnot_count += 1
            elif gate_name == 'COMMENT' or gate_name == 'MEASURE':
                pass  # Don't count
            else:
                self.other_count += 1
                
            # Track breakdown
            self.gate_breakdown[gate_name] = self.gate_breakdown.get(gate_name, 0) + 1
            
        return self.summary()
        
    def summary(self) -> Dict:
        """Return summary of gate counts."""
        return {
            'toffoli': self.toffoli_count,
            'cnot': self.cnot_count,
            'single_qubit': self.single_count,
            'other': self.other_count,
            'total': self.toffoli_count + self.cnot_count + self.single_count + self.other_count,
            'breakdown': self.gate_breakdown
        }
        
    @property
    def clifford_t_count(self) -> Dict:
        """Estimate Clifford+T decomposition."""
        # Toffoli = 7 T gates (optimal)
        # CNOT = Clifford (0 T)
        # Single qubit rotations ~ 1-3 T each
        return {
            't_gates': self.toffoli_count * 7 + self.single_count * 2,
            'clifford_gates': self.cnot_count + self.single_count + self.toffoli_count * 10
        }
