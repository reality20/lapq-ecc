"""
Phase 5: Checkpoint module for pebble-game strategy.
Enables space-time tradeoff in long scalar multiplications.
"""

from typing import List, Tuple


class PebbleCheckpoint:
    """
    Implements the sqrt(n) pebble game strategy.
    
    Stores intermediate states to reduce peak qubit usage at the cost of recomputation.
    For secp256k1 with 64 windows, uses 4-8 checkpoints.
    """
    
    def __init__(self, total_windows: int = 64, max_checkpoints: int = 4, 
                 register_size: int = 768):
        self.total_windows = total_windows
        self.max_checkpoints = max_checkpoints
        self.register_size = register_size  # 768 qubits per Jacobian point
        
        # Compute checkpoint positions using sqrt(n) strategy
        self.checkpoint_interval = total_windows // max_checkpoints
        self.checkpoint_positions = self._compute_positions()
        
    def _compute_positions(self) -> List[int]:
        """Compute optimal checkpoint positions."""
        return [i * self.checkpoint_interval for i in range(1, self.max_checkpoints + 1)]
        
    def should_checkpoint(self, window_index: int) -> bool:
        """Check if current window should trigger a checkpoint save."""
        return window_index in self.checkpoint_positions
        
    def get_checkpoint_index(self, window_index: int) -> int:
        """Get the checkpoint storage index for a given window."""
        try:
            return self.checkpoint_positions.index(window_index)
        except ValueError:
            return -1
            
    def generate_save_gates(self, source_reg: List[int], dest_reg: List[int]) -> List[Tuple]:
        """Generate SWAP gates to save register state to checkpoint storage."""
        if len(source_reg) != len(dest_reg):
            raise ValueError("Source and destination registers must match")
            
        gates = []
        for i in range(len(source_reg)):
            # Use CSWAP with control=0 (always swap for save)
            # In full impl, would use controlled SWAP network
            gates.append(('SWAP', source_reg[i], dest_reg[i]))
        return gates
        
    def generate_restore_gates(self, source_reg: List[int], dest_reg: List[int]) -> List[Tuple]:
        """Generate SWAP gates to restore from checkpoint."""
        return self.generate_save_gates(source_reg, dest_reg)  # SWAP is symmetric
        
    @property
    def checkpoint_storage_qubits(self) -> int:
        """Total qubits needed for checkpoint storage."""
        return self.max_checkpoints * self.register_size
        
    @property
    def space_time_tradeoff(self) -> dict:
        """Return analysis of space vs time tradeoff."""
        return {
            'checkpoints': self.max_checkpoints,
            'storage_qubits': self.checkpoint_storage_qubits,
            'recomputation_factor': self.checkpoint_interval,
            'peak_savings': f"~{self.checkpoint_interval * self.register_size} qubits"
        }
