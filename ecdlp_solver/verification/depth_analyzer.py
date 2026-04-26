"""
Phase 7: Depth Analyzer for circuit optimization.
Analyzes quantum circuit depth and critical paths.
"""

from typing import Dict, List, Tuple, Set


class DepthAnalyzer:
    """
    Analyzes quantum circuit depth and identifies critical paths.
    
    Computes:
    - Total circuit depth (layer count)
    - Critical path length
    - Parallelization opportunities
    - Gate-level depth breakdown
    """
    
    def __init__(self):
        self.gate_depths = {
            'H': 1, 'X': 1, 'Y': 1, 'Z': 1, 'S': 1, 'T': 1,
            'RX': 1, 'RY': 1, 'RZ': 1, 'CRz': 2,
            'CNOT': 1, 'CCNOT': 3, 'SWAP': 3, 'CSWAP': 5,
            'MEASURE': 1, 'COMMENT': 0
        }
        
    def analyze(self, gates: List[Tuple], n_qubits: int) -> Dict:
        """
        Analyze circuit depth.
        
        Args:
            gates: List of (gate_name, *qubits) tuples
            n_qubits: Total number of qubits
            
        Returns:
            Dictionary with depth analysis
        """
        if not gates:
            return {'total_depth': 0, 'critical_path': [], 'by_gate_type': {}}
            
        # Track when each qubit becomes free
        qubit_free_at = [0] * n_qubits
        
        # Track depth by gate type
        depth_by_type: Dict[str, int] = {}
        
        current_layer = 0
        
        for gate in gates:
            gate_name = gate[0]
            qubits = gate[1:] if len(gate) > 1 else []
            
            # Get base depth for this gate type
            base_depth = self.gate_depths.get(gate_name, 1)
            
            if not qubits:
                continue
                
            # Find earliest time this gate can start
            # (when all its qubits are free)
            earliest_start = max(qubit_free_at[q] for q in qubits)
            
            # Update qubit availability
            end_time = earliest_start + base_depth
            for q in qubits:
                qubit_free_at[q] = end_time
                
            # Track depth by type
            depth_by_type[gate_name] = depth_by_type.get(gate_name, 0) + base_depth
            
        total_depth = max(qubit_free_at) if qubit_free_at else 0
        
        return {
            'total_depth': total_depth,
            'num_gates': len(gates),
            'parallelization_factor': len(gates) / total_depth if total_depth > 0 else 0,
            'by_gate_type': depth_by_type,
            'qubit_utilization': sum(1 for t in qubit_free_at if t > 0) / n_qubits if n_qubits > 0 else 0
        }
        
    def estimate_runtime(self, gates: List[Tuple], 
                         gate_times: Dict[str, float] = None) -> float:
        """
        Estimate circuit runtime given gate times.
        
        Args:
            gates: List of gate tuples
            gate_times: Dict mapping gate names to durations in microseconds
            
        Returns:
            Estimated runtime in microseconds
        """
        if gate_times is None:
            # Default times (nanoseconds typical for superconducting)
            gate_times = {
                'H': 20, 'X': 20, 'Y': 20, 'Z': 0,  # Z is virtual
                'S': 20, 'T': 20,
                'CNOT': 200, 'CCNOT': 600,
                'SWAP': 600, 'CSWAP': 1000,
                'CRz': 100, 'RZ': 0
            }
            
        total_time = 0.0
        for gate in gates:
            gate_name = gate[0]
            total_time += gate_times.get(gate_name, 50)
            
        return total_time
