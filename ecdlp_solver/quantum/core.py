"""
Quantum circuit infrastructure for QPU-1 integration.

This module provides the foundational classes for building and executing
quantum circuits on the QPU-1 hardware backend.
"""

from typing import List, Tuple, Dict, Any, Optional
import math


class QuantumRegister:
    """
    A quantum register representing a collection of qubits.
    
    Parameters
    ----------
    size : int
        Number of qubits in the register
    name : str, optional
        Human-readable name for debugging
    """
    
    def __init__(self, size: int, name: str = ""):
        self.size = size
        self.name = name
        self._qubits = list(range(size))  # Placeholder for qubit indices
    
    def __getitem__(self, idx: int) -> int:
        """Get the global qubit index for position idx in this register."""
        return self._qubits[idx]
    
    def __len__(self) -> int:
        return self.size
    
    def __repr__(self) -> str:
        return f"QuantumRegister({self.size}, '{self.name}')"


class JacobianPointRegister:
    """
    A composite register for storing a point in Jacobian coordinates (X:Y:Z).
    
    Each coordinate is a 256-bit register for secp256k1.
    
    Parameters
    ----------
    base_index : int
        Starting qubit index for this point register
    name : str, optional
        Human-readable name for debugging
    """
    
    def __init__(self, base_index: int, name: str = ""):
        self.name = name
        self.x_reg = list(range(base_index, base_index + 256))
        self.y_reg = list(range(base_index + 256, base_index + 512))
        self.z_reg = list(range(base_index + 512, base_index + 768))
    
    @property
    def total_qubits(self) -> int:
        return 768
    
    @property
    def all_qubits(self) -> List[int]:
        return self.x_reg + self.y_reg + self.z_reg
    
    def __repr__(self) -> str:
        return f"JacobianPointRegister(768 qubits, '{self.name}')"


class AncillaPool:
    """
    Manages allocation and release of ancilla qubits.
    
    Tracks peak usage and ensures ancillae are properly returned to |0⟩.
    
    Parameters
    ----------
    pool_qubits : List[int]
        List of available ancilla qubit indices
    """
    
    def __init__(self, pool_qubits: List[int]):
        self._available = set(pool_qubits)
        self._allocated: Dict[int, List[int]] = {}  # allocation_id -> qubits
        self._next_id = 0
        self._peak_usage = 0
        self._current_usage = 0
    
    def allocate(self, count: int) -> List[int]:
        """
        Allocate count ancilla qubits from the pool.
        
        Returns
        -------
        List[int]
            List of allocated qubit indices
        
        Raises
        ------
        PoolExhaustedError
            If insufficient ancillae are available
        """
        if len(self._available) < count:
            raise PoolExhaustedError(
                f"Need {count} ancillae but only {len(self._available)} available"
            )
        
        allocated = []
        for _ in range(count):
            qubit = self._available.pop()
            allocated.append(qubit)
        
        alloc_id = self._next_id
        self._next_id += 1
        self._allocated[alloc_id] = allocated
        self._current_usage += count
        self._peak_usage = max(self._peak_usage, self._current_usage)
        
        return allocated
    
    def release(self, qubits: List[int]) -> None:
        """
        Release ancilla qubits back to the pool.
        
        Parameters
        ----------
        qubits : List[int]
            Qubit indices to release
        """
        for q in qubits:
            self._available.add(q)
            self._current_usage -= 1
        
        # Remove from allocated dict
        for alloc_id, allocated in list(self._allocated.items()):
            if all(q in allocated for q in qubits):
                del self._allocated[alloc_id]
                break
    
    @property
    def available(self) -> int:
        """Number of available ancilla qubits."""
        return len(self._available)
    
    @property
    def peak_usage(self) -> int:
        """Peak number of simultaneously allocated ancillae."""
        return self._peak_usage
    
    @property
    def current_usage(self) -> int:
        """Current number of allocated ancillae."""
        return self._current_usage
    
    def __repr__(self) -> str:
        return f"AncillaPool(available={self.available}, peak={self._peak_usage})"


class QuantumCircuit:
    """
    Quantum circuit builder and executor for QPU-1.
    
    Records gates and can generate Qreg code for execution on QPU-1.
    
    Parameters
    ----------
    num_qubits : int
        Total number of qubits in the circuit
    name : str, optional
        Circuit name for debugging
    """
    
    def __init__(self, num_qubits: int, name: str = "circuit"):
        self.num_qubits = num_qubits
        self.name = name
        self.gates: List[Tuple[str, List[int], List[Any]]] = []
        self._depth = 0
        self._gate_counts: Dict[str, int] = {}
    
    def _record_gate(self, gate_name: str, qubits: List[int], params: List[Any] = None) -> 'QuantumCircuit':
        """Record a gate and return self for method chaining."""
        if params is None:
            params = []
        
        self.gates.append((gate_name, qubits, params))
        
        # Update gate counts
        self._gate_counts[gate_name] = self._gate_counts.get(gate_name, 0) + 1
        
        return self
    
    def H(self, qubit: int) -> 'QuantumCircuit':
        """Apply Hadamard gate."""
        return self._record_gate("H", [qubit])
    
    def X(self, qubit: int) -> 'QuantumCircuit':
        """Apply Pauli-X gate."""
        return self._record_gate("X", [qubit])
    
    def Y(self, qubit: int) -> 'QuantumCircuit':
        """Apply Pauli-Y gate."""
        return self._record_gate("Y", [qubit])
    
    def Z(self, qubit: int) -> 'QuantumCircuit':
        """Apply Pauli-Z gate."""
        return self._record_gate("Z", [qubit])
    
    def S(self, qubit: int) -> 'QuantumCircuit':
        """Apply S gate (phase gate)."""
        return self._record_gate("S", [qubit])
    
    def T(self, qubit: int) -> 'QuantumCircuit':
        """Apply T gate (π/8 gate)."""
        return self._record_gate("T", [qubit])
    
    def Rx(self, qubit: int, theta: float) -> 'QuantumCircuit':
        """Apply rotation around X-axis."""
        return self._record_gate("Rx", [qubit], [theta])
    
    def Ry(self, qubit: int, theta: float) -> 'QuantumCircuit':
        """Apply rotation around Y-axis."""
        return self._record_gate("Ry", [qubit], [theta])
    
    def Rz(self, qubit: int, theta: float) -> 'QuantumCircuit':
        """Apply rotation around Z-axis."""
        return self._record_gate("Rz", [qubit], [theta])
    
    def CNOT(self, control: int, target: int) -> 'QuantumCircuit':
        """Apply CNOT gate."""
        return self._record_gate("CNOT", [control, target])
    
    def CCNOT(self, control1: int, control2: int, target: int) -> 'QuantumCircuit':
        """Apply Toffoli (CCNOT) gate."""
        return self._record_gate("CCNOT", [control1, control2, target])
    
    def SWAP(self, q1: int, q2: int) -> 'QuantumCircuit':
        """Apply SWAP gate."""
        return self._record_gate("SWAP", [q1, q2])
    
    def CZ(self, control: int, target: int) -> 'QuantumCircuit':
        """Apply controlled-Z gate."""
        return self._record_gate("CZ", [control, target])
    
    def CRz(self, control: int, target: int, theta: float) -> 'QuantumCircuit':
        """Apply controlled rotation around Z-axis."""
        return self._record_gate("CRz", [control, target], [theta])
    
    def measure(self, qubits: Optional[List[int]] = None) -> 'QuantumCircuit':
        """
        Add measurement operations.
        
        Parameters
        ----------
        qubits : List[int], optional
            Qubits to measure. If None, measure all qubits.
        """
        if qubits is None:
            qubits = list(range(self.num_qubits))
        return self._record_gate("MEASURE", qubits)
    
    def barrier(self) -> 'QuantumCircuit':
        """Add a barrier for visualization/optimization."""
        return self._record_gate("BARRIER", [])
    
    def to_qreg(self, auto_measure: bool = True) -> str:
        """
        Generate Qreg code for execution on QPU-1 with correct syntax.
        
        Parameters
        ----------
        auto_measure : bool
            If True, add measurement at the end
            
        Returns
        -------
        str
            Qreg source code
        """
        lines = [f"# Quantum circuit: {self.name}", f"q = Qreg({self.num_qubits})", ""]
        
        for gate in self.gates:
            gate_name = gate[0]
            qubits = gate[1:-1] if len(gate) > 2 and isinstance(gate[-1], (int, float)) else gate[1:]
            params = [] if len(gate) <= 2 or not isinstance(gate[-1], (int, float)) else [gate[-1]]
            if gate_name == "BARRIER":
                lines.append("# BARRIER")
                continue
            
            if gate_name == "MEASURE":
                continue  # Handle at the end
            
            # Generate gate call with QPU-1 syntax: q.GATE(q0, q1, ..., params)
            all_args = [str(q) for q in qubits] + [str(p) for p in params]
            args_str = ", ".join(all_args)
            
            if args_str:
                lines.append(f"q.{gate_name}({args_str})")
            else:
                lines.append(f"q.{gate_name}()")
        
        if auto_measure:
            lines.append("")
            lines.append("# Measure all qubits")
            lines.append(f"print(q.measure())")
        
        return "\n".join(lines)
    
    def get_gate_count(self, gate_type: Optional[str] = None) -> int:
        """
        Get count of specific gate type or total gates.
        
        Parameters
        ----------
        gate_type : str, optional
            Gate name to count. If None, return total gate count.
        """
        if gate_type is None:
            return sum(self._gate_counts.values())
        return self._gate_counts.get(gate_type, 0)
    
    def gate_count(self) -> int:
        """Alias for get_gate_count() - returns total gate count."""
        return self.get_gate_count()
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get gate statistics as a dictionary."""
        return {
            'toffoli_count': self._gate_counts.get('CCNOT', 0),
            'cnot_count': self._gate_counts.get('CNOT', 0),
            'single_qubit_count': sum(
                self._gate_counts.get(g, 0) 
                for g in ['H', 'X', 'Y', 'Z', 'S', 'T', 'Rx', 'Ry', 'Rz']
            ),
            'rotation_count': self._gate_counts.get('CRz', 0),
            'swap_count': self._gate_counts.get('SWAP', 0),
        }
    
    def get_depth(self) -> int:
        """Estimate circuit depth (simplified)."""
        # Simple depth estimation: count sequential layers
        # A proper implementation would do dependency analysis
        return len(self.gates)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get circuit statistics."""
        return {
            "num_qubits": self.num_qubits,
            "total_gates": self.get_gate_count(),
            "gate_counts": dict(self._gate_counts),
            "depth": self.get_depth(),
        }
    
    def __repr__(self) -> str:
        return f"QuantumCircuit({self.num_qubits} qubits, {self.get_gate_count()} gates)"


class PoolExhaustedError(Exception):
    """Raised when ancilla pool is exhausted."""
    pass


class InvalidCircuitError(Exception):
    """Raised when a circuit has invalid structure."""
    pass


class VerificationError(Exception):
    """Raised when verification fails."""
    pass
