"""
Controlled SWAP (Fredkin) gate implementation.
"""


class CSWAP:
    """
    Controlled SWAP gate (Fredkin gate).
    
    Swaps two qubits/registers conditioned on a control qubit.
    Decomposes into 2 CNOTs and 1 Toffoli.
    """
    
    def __init__(self):
        self.toffoli_count = 1
        self.cnot_count = 2
    
    def apply(self, circuit, ctrl: int, q1: int, q2: int) -> None:
        """
        Apply CSWAP to two qubits.
        
        If ctrl = 1: swap q1 and q2
        If ctrl = 0: no change
        
        Decomposition:
        1. CNOT(q2, q1)
        2. CCNOT(ctrl, q1, q2)
        3. CNOT(q2, q1)
        """
        circuit.CNOT(q2, q1)
        circuit.CCNOT(ctrl, q1, q2)
        circuit.CNOT(q2, q1)
    
    def apply_register(self, circuit, ctrl: int, 
                       reg1: list[int], reg2: list[int]) -> None:
        """
        Apply CSWAP to two registers (bitwise swap).
        
        Each bit pair is swapped independently.
        """
        for q1, q2 in zip(reg1, reg2):
            self.apply(circuit, ctrl, q1, q2)


def cswap_decompose(ctrl: int, q1: int, q2: int) -> list[tuple]:
    """
    Return gate decomposition of CSWAP.
    
    Returns list of (gate_name, qubit_indices) tuples.
    """
    return [
        ('CNOT', (q2, q1)),
        ('CCNOT', (ctrl, q1, q2)),
        ('CNOT', (q2, q1)),
    ]
