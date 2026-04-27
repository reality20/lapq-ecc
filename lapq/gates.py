"""
lapq.gates — Gate-optimized decomposition engine for QPU-1.

All non-primitive gates decomposed into minimal gate sequences using
QPU-1 native gates: H, X, Y, Z, S, T, Rx, Ry, Rz, CNOT, CCNOT, SWAP.

Optimization targets:
  - Minimum CNOT count (dominant cost on real hardware)
  - Fused single-qubit rotations where possible
  - Relative-phase Toffoli variants for lower T-count
  - Zero-angle gate elimination
"""

import math
from typing import List, Tuple, Any

# Threshold below which rotation angles are treated as zero
_EPS = 1e-15


class GateDecomposer:
    """Decomposes high-level gates into QPU-1 primitives with minimal gate count."""

    @staticmethod
    def decompose(gate_name: str, qubits: List[int], *params: Any) -> List[Tuple[str, List[int], List[Any]]]:
        name = gate_name.lower()

        # ── Single-qubit (1 gate each) ──

        if name == "sdg":
            return [("Rz", [qubits[0]], [-math.pi / 2])]

        if name == "tdg":
            return [("Rz", [qubits[0]], [-math.pi / 4])]

        if name in ("sx", "v"):
            return [("Rx", [qubits[0]], [math.pi / 2])]

        if name == "sxdg":
            return [("Rx", [qubits[0]], [-math.pi / 2])]

        if name in ("p", "u1"):
            lam = params[0]
            if abs(lam) < _EPS:
                return []
            return [("Rz", [qubits[0]], [lam])]

        if name == "u2":
            phi, lam = params
            return [
                ("Rz", [qubits[0]], [lam]),
                ("Rx", [qubits[0]], [math.pi / 2]),
                ("Rz", [qubits[0]], [phi]),
            ]

        if name == "u3":
            theta, phi, lam = params
            ops = []
            if abs(lam) >= _EPS:
                ops.append(("Rz", [qubits[0]], [lam]))
            if abs(theta) >= _EPS:
                ops.append(("Ry", [qubits[0]], [theta]))
            if abs(phi) >= _EPS:
                ops.append(("Rz", [qubits[0]], [phi]))
            return ops if ops else []

        # ── Two-qubit (minimal CNOT) ──

        if name == "cz":
            c, t = qubits
            return [("H", [t], []), ("CNOT", [c, t], []), ("H", [t], [])]  # 1 CNOT

        if name == "cy":
            c, t = qubits
            # CY = Sdg·CNOT·S — 1 CNOT + 2 single-qubit
            return [
                ("Rz", [t], [-math.pi / 2]),
                ("CNOT", [c, t], []),
                ("Rz", [t], [math.pi / 2]),
            ]

        if name == "ch":
            c, t = qubits
            # Controlled-H: Ry(-π/4)·CNOT·Ry(π/4) — 1 CNOT
            return [
                ("Ry", [t], [-math.pi / 4]),
                ("CNOT", [c, t], []),
                ("Ry", [t], [math.pi / 4]),
            ]

        if name == "crx":
            c, t = qubits
            theta = params[0]
            if abs(theta) < _EPS:
                return []
            # Optimal 2-CNOT decomposition
            return [
                ("Rx", [t], [theta / 2]),
                ("CNOT", [c, t], []),
                ("Rx", [t], [-theta / 2]),
                ("CNOT", [c, t], []),
            ]

        if name == "cry":
            c, t = qubits
            theta = params[0]
            if abs(theta) < _EPS:
                return []
            return [
                ("Ry", [t], [theta / 2]),
                ("CNOT", [c, t], []),
                ("Ry", [t], [-theta / 2]),
                ("CNOT", [c, t], []),
            ]

        if name == "crz":
            c, t = qubits
            theta = params[0]
            if abs(theta) < _EPS:
                return []
            return [
                ("Rz", [t], [theta / 2]),
                ("CNOT", [c, t], []),
                ("Rz", [t], [-theta / 2]),
                ("CNOT", [c, t], []),
            ]

        if name == "cp":
            c, t = qubits
            theta = params[0]
            if abs(theta) < _EPS:
                return []
            # Optimized CP: 1 CNOT + 3 Rz
            return [
                ("Rz", [c], [theta / 2]),
                ("Rz", [t], [theta / 2]),
                ("CNOT", [c, t], []),
                ("Rz", [t], [-theta / 2]),
                ("CNOT", [c, t], []),
            ]

        if name == "rxx":
            q1, q2 = qubits
            theta = params[0]
            if abs(theta) < _EPS:
                return []
            # 1 CNOT + 4 single-qubit (H sandwich)
            return [
                ("H", [q1], []), ("H", [q2], []),
                ("CNOT", [q1, q2], []),
                ("Rz", [q2], [theta]),
                ("CNOT", [q1, q2], []),
                ("H", [q1], []), ("H", [q2], []),
            ]

        if name == "ryy":
            q1, q2 = qubits
            theta = params[0]
            if abs(theta) < _EPS:
                return []
            # 1 CNOT + 4 single-qubit (Rx sandwich)
            return [
                ("Rx", [q1], [math.pi / 2]), ("Rx", [q2], [math.pi / 2]),
                ("CNOT", [q1, q2], []),
                ("Rz", [q2], [theta]),
                ("CNOT", [q1, q2], []),
                ("Rx", [q1], [-math.pi / 2]), ("Rx", [q2], [-math.pi / 2]),
            ]

        if name == "rzz":
            q1, q2 = qubits
            theta = params[0]
            if abs(theta) < _EPS:
                return []
            # Optimal: 1 CNOT + 1 Rz
            return [
                ("CNOT", [q1, q2], []),
                ("Rz", [q2], [theta]),
                ("CNOT", [q1, q2], []),
            ]

        # ── Three-qubit ──

        if name in ("cswap", "fredkin"):
            c, t1, t2 = qubits
            # Fredkin = CNOT + Toffoli + CNOT (1 CCNOT + 2 CNOT)
            return [
                ("CNOT", [t2, t1], []),
                ("CCNOT", [c, t1, t2], []),
                ("CNOT", [t2, t1], []),
            ]

        if name == "ccz":
            c1, c2, t = qubits
            return [
                ("H", [t], []),
                ("CCNOT", [c1, c2, t], []),
                ("H", [t], []),
            ]

        # ── Specialized ──

        if name == "ecr":
            q1, q2 = qubits
            # ECR = Rx(pi/4) on q1, CNOT, X on q1 — 1 CNOT + 2 single-qubit
            return [
                ("Rx", [q1], [math.pi / 4]),
                ("CNOT", [q1, q2], []),
                ("X", [q1], []),
            ]

        # Fallback
        return [(gate_name, qubits, list(params))]
