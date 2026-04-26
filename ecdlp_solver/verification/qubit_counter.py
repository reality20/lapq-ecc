"""
Phase 7: Qubit Tracker for resource estimation.
Tracks qubit allocation and peak usage in quantum circuits.
"""

from typing import Dict, List, Set


class QubitTracker:
    """
    Tracks qubit usage throughout a quantum circuit.
    
    Monitors:
    - Total qubits allocated
    - Peak simultaneous usage
    - Qubit reuse patterns
    - Ancilla vs logical qubit distinction
    """
    
    def __init__(self, total_qubits: int = 0):
        self.total_qubits = total_qubits
        self.allocated: Set[int] = set()
        self.released: Set[int] = set()
        self.peak_usage = 0
        self.current_usage = 0
        self.qubit_history: List[int] = []
        
    def allocate(self, qubit_id: int) -> None:
        """Mark a qubit as allocated."""
        if qubit_id not in self.allocated:
            self.allocated.add(qubit_id)
            self.current_usage += 1
            self.peak_usage = max(self.peak_usage, self.current_usage)
            self.qubit_history.append(self.current_usage)
            
    def allocate_range(self, start: int, count: int) -> List[int]:
        """Allocate a range of qubits."""
        qubits = list(range(start, start + count))
        for q in qubits:
            self.allocate(q)
        return qubits
        
    def release(self, qubit_id: int) -> None:
        """Mark a qubit as released (can be reused)."""
        if qubit_id in self.allocated and qubit_id not in self.released:
            self.released.add(qubit_id)
            self.current_usage -= 1
            self.qubit_history.append(self.current_usage)
            
    def release_range(self, start: int, count: int) -> None:
        """Release a range of qubits."""
        for i in range(count):
            self.release(start + i)
            
    def is_available(self, qubit_id: int) -> bool:
        """Check if a qubit is available for allocation."""
        return qubit_id in self.released or qubit_id not in self.allocated
        
    def summary(self) -> Dict:
        """Return summary of qubit tracking."""
        return {
            'total_qubits': self.total_qubits,
            'allocated': len(self.allocated),
            'released': len(self.released),
            'currently_in_use': self.current_usage,
            'peak_usage': self.peak_usage,
            'available_for_reuse': len(self.released),
            'utilization': self.peak_usage / self.total_qubits if self.total_qubits > 0 else 0
        }
        
    def reset(self) -> None:
        """Reset tracker state."""
        self.allocated.clear()
        self.released.clear()
        self.peak_usage = 0
        self.current_usage = 0
        self.qubit_history.clear()
