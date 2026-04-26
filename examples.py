"""
lapq/examples.py — Annotated examples for the lapq library.

Run this file to see all examples printed to stdout (no API key needed for code generation).
"""

import math


def _show(title: str, c) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)
    print(c.to_qreg())
    print(f"  >> Gates: {c.gate_count()}")


def demo_without_api_key() -> None:
    """All examples below generate circuits without needing an API key."""
    from lapq.circuit import Circuit

    def circuit(n): return Circuit(n, client=None)

    # ── Beginner examples ──────────────────────────────────────────────────

    _show("Bell State (|00⟩ + |11⟩)/√2",
          circuit(2).bell_pair(0, 1))

    _show("GHZ State (5 qubits)",
          circuit(5).ghz())

    _show("W State (3 qubits)",
          circuit(3).w_state())

    _show("Quantum Teleportation",
          circuit(3).h(0).teleport(0, 1, 2))

    _show("Superdense Coding (message='11')",
          circuit(2).h(0).cx(0, 1).superdense_encode(0, 1, "11"))

    # ── Intermediate examples ──────────────────────────────────────────────

    _show("QFT on 4 qubits",
          circuit(4).qft())

    _show("Inverse QFT on 4 qubits",
          circuit(4).iqft())

    _show("Cluster State (4 qubits)",
          circuit(4).cluster_state())

    _show("Grover Diffusion Operator (3 qubits)",
          circuit(3).h(0).h(1).h(2).grover_diffusion())

    _show("SWAP Test (3 qubits)",
          circuit(3).h(1).h(2).swap_test(0, 1, 2))

    # ── Extended gate set (auto-decomposed) ───────────────────────────────

    _show("CZ Gate (decomposed)",
          circuit(2).cz(0, 1))

    _show("CY Gate (decomposed)",
          circuit(2).cy(0, 1))

    _show("CRx(π/4) Gate (decomposed)",
          circuit(2).crx(0, 1, math.pi / 4))

    _show("Fredkin / CSWAP (decomposed)",
          circuit(3).cswap(0, 1, 2))

    _show("CCZ Gate (decomposed)",
          circuit(3).ccz(0, 1, 2))

    _show("iSWAP Gate (decomposed)",
          circuit(2).iswap(0, 1))

    _show("U3(π/3, π/4, π/5) Gate",
          circuit(1).u3(0, math.pi/3, math.pi/4, math.pi/5))

    _show("CS Gate (Controlled-S, decomposed)",
          circuit(2).cs(0, 1))

    _show("RZZ(π/2) Ising Gate",
          circuit(2).rzz(0, 1, math.pi / 2))

    # ── Algorithm factories ────────────────────────────────────────────────
    # Algorithms work by building Circuit objects. We verify them with a stub
    # client that has a circuit() factory but no real HTTP calls.
    class _Stub:
        def circuit(self, n): return circuit(n)

    stub = _Stub()

    from lapq import algorithms as alg

    _show("Grover's Search (n=3, mark=5)",
          alg.grover(stub, 3, [5], iterations=1))

    _show("QAOA MaxCut (triangle)",
          alg.qaoa_maxcut(stub, [(0,1),(1,2),(2,0)], p=1))

    _show("VQE Molecular (4 qubits)",
          alg.vqe_molecular(stub, 4))

    _show("Shor's Period Finding (a=7, N=15)",
          alg.shors_period_finding(stub, 7, 15))

    _show("Deutsch-Jozsa (n=3, balanced)",
          alg.deutsch_jozsa(stub, 3, constant=False))

    _show("Bernstein-Vazirani (n=4, secret=0b1011)",
          alg.bernstein_vazirani(stub, 4, secret=0b1011))

    _show("HHL Quantum Linear Solver",
          alg.harrow_hassidim_lloyd(stub, n_b=2, n_clock=3))

    _show("Option Pricing (4-bit register)",
          alg.option_pricing_quantum(stub, n_bits=4))

    _show("Quantum Teleportation (via algorithms module)",
          alg.quantum_teleportation(stub))

    _show("Heisenberg Model (4 spins)",
          alg.heisenberg_model(stub, 4, J=1.0, time=1.0))

    _show("Continuous Quantum Walk (4 nodes)",
          alg.continuous_quantum_walk(stub, 4, time=1.0))

    _show("Randomized Benchmarking (depth=4)",
          alg.randomized_benchmarking(stub, n_qubits=1, depth=4))



if __name__ == "__main__":
    demo_without_api_key()
    print("\n\n✅ All circuit examples generated successfully!")
    print("   To run on QPU-1: qpu.circuit(...).run()")
    print("   Get API key at:  https://qpu-1.lovable.app/api-access")
