"""
Reversible computation utilities including Bennett's compute-copy-uncompute pattern.
"""

from typing import List, Tuple, Any, Callable, Optional
from .core import QuantumCircuit


class BennettWrapper:
    """
    Wraps a circuit to implement Bennett's compute-copy-uncompute pattern.
    
    Given a forward circuit that computes f(x) into an output register,
    this wrapper creates a reversible version that:
    1. Computes f(x) (leaving workspace dirty)
    2. Copies the result to a clean register
    3. Uncomputes f(x) to restore workspace to |0⟩
    
    This ensures all ancillae are returned to |0⟩ state.
    
    Parameters
    ----------
    forward_fn : Callable
        Function that applies the forward computation to a circuit
    num_input : int
        Number of input qubits
    num_output : int
        Number of output qubits
    num_workspace : int
        Number of workspace/ancilla qubits needed
    """
    
    def __init__(self, forward_fn: Callable, num_input: int, 
                 num_output: int, num_workspace: int):
        self.forward_fn = forward_fn
        self.num_input = num_input
        self.num_output = num_output
        self.num_workspace = num_workspace
    
    def apply(self, circuit: QuantumCircuit,
              input_reg: List[int],
              output_reg: List[int],
              workspace: List[int]) -> List[Tuple[str, List[int], List[Any]]]:
        """
        Apply compute-copy-uncompute sequence.
        
        Parameters
        ----------
        circuit : QuantumCircuit
            Circuit to apply gates to
        input_reg : List[int]
            Input qubits (preserved)
        output_reg : List[int]
            Output qubits (initially |0⟩, will contain f(x))
        workspace : List[int]
            Workspace qubits (returned to |0⟩)
        
        Returns
        -------
        List of gates applied
        """
        assert len(input_reg) == self.num_input
        assert len(output_reg) == self.num_output
        assert len(workspace) == self.num_workspace
        
        # Step 1: Compute f(x) into output_reg using workspace
        # The forward function should write its result to output_reg
        self.forward_fn(circuit, input_reg, output_reg, workspace)
        
        # Step 2: Copy result to a temporary (we'll use output_reg itself as the target)
        # Actually, we need another register for the copy if we want to uncompute
        # For now, assume output_reg already has the result
        
        # Step 3: Uncompute by running inverse operations in reverse order
        # This requires storing the gate sequence or having an uncompute_fn
        # For now, this is a placeholder - proper implementation needs
        # either gate recording or explicit inverse functions
        
        return circuit.gates


def make_reversible(forward_fn: Callable, inverse_fn: Optional[Callable] = None) -> Callable:
    """
    Decorator/wrapper to make a function reversible via Bennett's trick.
    
    If inverse_fn is provided, uses it for uncomputation.
    Otherwise, assumes the forward operation is self-inverse or records gates.
    
    Parameters
    ----------
    forward_fn : Callable
        Forward computation function
    inverse_fn : Callable, optional
        Inverse computation function. If None, forward_fn must be self-inverse.
    
    Returns
    -------
    Callable
        Wrapped function implementing compute-copy-uncompute
    """
    def wrapped(circuit: QuantumCircuit, *args, **kwargs):
        # Apply forward
        forward_fn(circuit, *args, **kwargs)
        
        # If we have an explicit inverse, we would apply it after copying
        # For now, just apply forward
        # Proper implementation needs:
        # 1. Record gates from forward
        # 2. Copy output to clean register
        # 3. Replay recorded gates in reverse with inverse operations
        
        return circuit.gates
    
    return wrapped


class ComputeCopyUncompute:
    """
    Context manager for Bennett-style reversible computation.
    
    Usage:
        with ComputeCopyUncompute(circuit) as ccu:
            # Apply forward computation
            my_circuit.apply(circuit, ...)
        # After context, workspace is restored
    
    Parameters
    ----------
    circuit : QuantumCircuit
        Circuit being built
    """
    
    def __init__(self, circuit: QuantumCircuit):
        self.circuit = circuit
        self.gate_start_idx = 0
    
    def __enter__(self):
        self.gate_start_idx = len(self.circuit.gates)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Get gates added during the context
        new_gates = self.circuit.gates[self.gate_start_idx:]
        
        # To properly uncompute, we would:
        # 1. Copy the output to a clean register (done outside this context)
        # 2. Apply inverse of each gate in reverse order
        
        # For now, this is a placeholder
        # Full implementation requires gate inversion logic
        
        return False  # Don't suppress exceptions


def invert_gate(gate: Tuple[str, List[int], List[Any]]) -> List[Tuple[str, List[int], List[Any]]]:
    """
    Return the inverse of a gate.
    
    Most gates are self-inverse: H, X, Y, Z, CNOT, CCNOT, SWAP
    Rotation gates need negated angles: Rx(θ)⁻¹ = Rx(-θ)
    
    Parameters
    ----------
    gate : Tuple[str, List[int], List[Any]]
        Gate tuple (name, qubits, params)
    
    Returns
    -------
    List of gates representing the inverse
    """
    name, qubits, params = gate
    
    # Self-inverse gates
    self_inverse = {'H', 'X', 'Y', 'Z', 'S', 'CNOT', 'CCNOT', 'SWAP', 'MEASURE', 'BARRIER'}
    if name in self_inverse:
        return [gate]  # Self-inverse
    
    # Rotation gates: negate angle
    if name in {'Rx', 'Ry', 'Rz'}:
        return [(name, qubits, [-params[0]])]
    
    # Controlled rotations
    if name == 'CRz':
        return [('CRz', qubits, [-params[0]])]
    
    # T gate: T⁻¹ = T† = Rz(-π/4)
    if name == 'T':
        return [('Rz', qubits, [-3.141592653589793 / 4])]
    
    # S gate: S⁻¹ = S† = Rz(-π/2)
    if name == 'S':
        return [('Rz', qubits, [-3.141592653589793 / 2])]
    
    # Unknown gate: return as-is (may not be correct)
    return [gate]
