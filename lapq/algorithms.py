"""
lapq.algorithms — Ready-made quantum algorithm factories for QPU-1.

Each function returns a Circuit object that can be inspected or executed.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from lapq.client import QPU1
    from lapq.circuit import Circuit


def bell_state(qpu, q1: int = 0, q2: int = 1):
    """Create a Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2."""
    return qpu.circuit(max(q1, q2) + 1).h(q1).cnot(q1, q2)


def ghz(qpu, n: int = 3):
    """Create an n-qubit GHZ state."""
    return qpu.circuit(n).ghz()


def grover(qpu, n: int = 3, marked: Union[int, List[int]] = 0, iterations: int = 1):
    """
    Grover search on n qubits marking given state(s).

    Parameters
    ----------
    qpu : QPU1 or stub
    n : int
        Number of data qubits.
    marked : int or list of int
        Target state(s) to mark.
    iterations : int
        Number of Grover iterations.
    """
    if isinstance(marked, int):
        marked = [marked]
    target = marked[0] % (2 ** n)

    c = qpu.circuit(n + 1)
    qs = list(range(n))
    anc = n

    # Initialize superposition
    for q in qs:
        c.h(q)
    c.x(anc).h(anc)

    for _ in range(iterations):
        # Oracle: flip |target⟩
        bits = format(target, f"0{n}b")
        for i, b in enumerate(bits):
            if b == "0":
                c.x(qs[i])
        if n >= 2:
            c.ccnot(qs[0], qs[1], anc)
        for i, b in enumerate(bits):
            if b == "0":
                c.x(qs[i])

        # Diffusion
        c.grover_diffusion(qs)

    return c


def qft_circuit(qpu, n: int = 4):
    """Create a QFT circuit on n qubits."""
    return qpu.circuit(n).qft()


def teleport(qpu):
    """Create a quantum teleportation circuit."""
    return qpu.circuit(3).h(0).teleport(0, 1, 2)


def quantum_teleportation(qpu):
    """Alias for teleport."""
    return teleport(qpu)


def qaoa_maxcut(qpu, edges: List[Tuple[int, int]], p: int = 1, gamma: float = 0.5, beta: float = 0.3):
    """
    QAOA for MaxCut problem.
    """
    nodes = set()
    for u, v in edges:
        nodes.add(u)
        nodes.add(v)
    n = max(nodes) + 1

    c = qpu.circuit(n)
    # Initial superposition
    for q in range(n):
        c.h(q)

    for _ in range(p):
        # Cost layer: exp(-i * gamma * C)
        for u, v in edges:
            c.rzz(u, v, 2 * gamma)

        # Mixer layer: exp(-i * beta * B)
        for q in range(n):
            c.rx(q, 2 * beta)

    return c


def vqe_molecular(qpu, n_qubits: int = 4, theta: float = 0.1):
    """
    Simple VQE ansatz circuit for molecular simulation.
    """
    c = qpu.circuit(n_qubits)
    # HF state: first half qubits excited
    for q in range(n_qubits // 2):
        c.x(q)
    # Parameterized gates
    for q in range(n_qubits - 1):
        c.ry(q, theta)
        c.cnot(q, q + 1)
    c.ry(n_qubits - 1, theta)
    return c


def shors_period_finding(qpu, a: int = 7, N: int = 15, n_counting: int = 0):
    """
    Simplified Shor's period finding circuit.
    """
    import math
    n = max(4, math.ceil(math.log2(N + 1)))
    if n_counting == 0:
        n_counting = 2 * n
    total = n_counting + n

    c = qpu.circuit(total)
    # Counting register superposition
    for q in range(n_counting):
        c.h(q)
    # Initialize work register to |1⟩
    c.x(n_counting)
    # Controlled modular exponentiation (simplified)
    for q in range(n_counting):
        c.cnot(q, n_counting)
    # Inverse QFT on counting register
    c.iqft(list(range(n_counting)))
    return c


def deutsch_jozsa(qpu, n: int = 3, constant: bool = False):
    """
    Deutsch-Jozsa algorithm.
    """
    c = qpu.circuit(n + 1)
    qs = list(range(n))
    anc = n

    c.x(anc).h(anc)
    for q in qs:
        c.h(q)

    # Oracle
    if constant:
        pass  # f(x) = 0, do nothing
    else:
        # Balanced: XOR of all bits
        for q in qs:
            c.cnot(q, anc)

    for q in qs:
        c.h(q)
    return c


def bernstein_vazirani(qpu, n: int = 4, secret: int = 0b1011):
    """
    Bernstein-Vazirani algorithm to find hidden bit-string.
    """
    c = qpu.circuit(n + 1)
    qs = list(range(n))
    anc = n

    c.x(anc).h(anc)
    for q in qs:
        c.h(q)

    # Oracle: f(x) = s·x mod 2
    for i in range(n):
        if (secret >> i) & 1:
            c.cnot(qs[i], anc)

    for q in qs:
        c.h(q)
    return c


def harrow_hassidim_lloyd(qpu, n_b: int = 2, n_clock: int = 3):
    """
    Simplified HHL (Quantum Linear Solver) circuit structure.
    """
    total = n_b + n_clock + 1  # +1 for ancilla
    c = qpu.circuit(total)

    b_reg = list(range(n_b))
    clock_reg = list(range(n_b, n_b + n_clock))
    anc = total - 1

    # Prepare |b⟩
    c.h(b_reg[0])

    # QPE
    for q in clock_reg:
        c.h(q)
    for i, q in enumerate(clock_reg):
        c.crz(q, b_reg[0], math.pi / (2 ** i))

    # Inverse QFT on clock
    c.iqft(clock_reg)

    # Controlled rotation
    for q in clock_reg:
        c.cry(q, anc, math.pi / 4)

    # Uncompute QPE
    c.qft(clock_reg)
    for i, q in reversed(list(enumerate(clock_reg))):
        c.crz(q, b_reg[0], -math.pi / (2 ** i))
    for q in clock_reg:
        c.h(q)

    return c


def option_pricing_quantum(qpu, n_bits: int = 4, strike: float = 0.5):
    """
    Quantum option pricing via amplitude estimation structure.
    """
    c = qpu.circuit(n_bits + 1)
    qs = list(range(n_bits))
    anc = n_bits

    # Load probability distribution (uniform for simplicity)
    for q in qs:
        c.h(q)

    # Payoff function (simplified comparator + rotation)
    for q in qs:
        c.cry(q, anc, math.pi / (2 ** (q + 1)))

    return c


def heisenberg_model(qpu, n_spins: int = 4, J: float = 1.0, time: float = 1.0, steps: int = 1):
    """
    Trotterized Heisenberg model simulation.
    """
    c = qpu.circuit(n_spins)
    dt = time / steps

    for _ in range(steps):
        for i in range(n_spins - 1):
            c.rxx(i, i + 1, J * dt)
            c.ryy(i, i + 1, J * dt)
            c.rzz(i, i + 1, J * dt)

    return c


def continuous_quantum_walk(qpu, n_nodes: int = 4, time: float = 1.0, steps: int = 1):
    """
    Continuous-time quantum walk on a line graph.
    """
    c = qpu.circuit(n_nodes)
    dt = time / steps

    # Start at node 0
    c.x(0)

    for _ in range(steps):
        for i in range(n_nodes - 1):
            c.rxx(i, i + 1, dt)
            c.ryy(i, i + 1, dt)

    return c


def randomized_benchmarking(qpu, n_qubits: int = 1, depth: int = 4, seed: int = 42):
    """
    Randomized benchmarking circuit — random Clifford sequence.
    """
    import random
    rng = random.Random(seed)

    c = qpu.circuit(n_qubits)
    cliffords = ["h", "s", "x", "y", "z"]

    for _ in range(depth):
        gate = rng.choice(cliffords)
        for q in range(n_qubits):
            getattr(c, gate)(q)

    return c
