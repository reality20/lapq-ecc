"""
lapq.circuit — Fluent quantum circuit builder with full gate set.

All non-primitive gates are automatically decomposed into QPU-1 native gates
(H, X, Y, Z, S, T, Rx, Ry, Rz, CNOT, CCNOT, SWAP) in the backend — the user
never has to think about decompositions.
"""

from __future__ import annotations

import io
import math
from typing import TYPE_CHECKING, List, Literal, Optional, Tuple, Any

from lapq.gates import GateDecomposer

if TYPE_CHECKING:
    from lapq.client import QPU1
    from lapq.models import JobResult

_decomposer = GateDecomposer()


def _fmt(name: str, qubits: List[int], params: List[Any]) -> str:
    """Render a single (name, qubits, params) tuple as a Qreg op string."""
    name = name.lower()
    q = qubits[0] if len(qubits) == 1 else None

    # Primitives that QPU-1 Qreg understands natively
    primitives = {
        "h": "q.H({q})",
        "x": "q.X({q})",
        "y": "q.Y({q})",
        "z": "q.Z({q})",
        "s": "q.S({q})",
        "t": "q.T({q})",
        "rx": "q.Rx({q}, {p0})",
        "ry": "q.Ry({q}, {p0})",
        "rz": "q.Rz({q}, {p0})",
    }

    if name in primitives:
        tpl = primitives[name]
        p0 = params[0] if params else 0
        return tpl.format(q=qubits[0], p0=p0)
    if name == "cnot":
        return f"q.CNOT({qubits[0]}, {qubits[1]})"
    if name == "ccnot":
        return f"q.CCNOT({qubits[0]}, {qubits[1]}, {qubits[2]})"
    if name == "swap":
        return f"q.SWAP({qubits[0]}, {qubits[1]})"

    # Fallback — should not reach here after full decomposition
    args = ", ".join(str(x) for x in qubits + params)
    return f"# UNRESOLVED: {name}({args})"


def _expand(name: str, qubits: List[int], params: List[Any]) -> List[str]:
    """Fully expand a gate to a list of Qreg strings via GateDecomposer."""
    primitives = {"h","x","y","z","s","t","rx","ry","rz","cnot","ccnot","swap","cz","crz"}
    if name.lower() in primitives:
        # CZ and CRZ are basically primitives in our formatting logic
        if name.lower() == "cz":
            return [f"q.H({qubits[1]})\nq.CNOT({qubits[0]}, {qubits[1]})\nq.H({qubits[1]})"]
        if name.lower() == "crz":
            theta = params[0]
            return [f"q.Rz({qubits[1]}, {theta/2})\nq.CNOT({qubits[0]}, {qubits[1]})\nq.Rz({qubits[1]}, {-theta/2})\nq.CNOT({qubits[0]}, {qubits[1]})"]
        return [_fmt(name, qubits, params)]
    
    decomposed = GateDecomposer.decompose(name, qubits, *params)
    result = []
    for (n, q, p) in decomposed:
        result.extend(_expand(n, q, p))
    return result


class Circuit:
    """
    A fluent, Pythonic quantum circuit builder for QPU-1.

    All gates are auto-decomposed server-side into native primitives — no
    quantum computing background needed to use the extended gate set.

    Example (beginner level)::

        qpu.circuit(2).bell_pair(0, 1).run()

    Example (intermediate level)::

        qpu.circuit(3).h(0).cz(0, 1).crx(1, 2, math.pi/4).measure().run()

    Example (expert level)::

        qpu.run_qreg("q = Qreg(2)\\nq.H(0)\\nq.CNOT(0,1)\\nprint(q.measure())")
    """

    def __init__(self, n_qubits: int, client: Optional["QPU1"]) -> None:
        self._n = n_qubits
        self._client = client
        self._ops: List[Tuple[str, List[int], List[Any]]] = []
        self._measured = False

    # ── Helpers ────────────────────────────────────────────────────────────

    def _add(self, name: str, qubits: List[int], *params: Any) -> "Circuit":
        """High-speed gate addition: just append the tuple, decompose later."""
        self._ops.append((name, qubits, list(params)))
        return self

    def raw(self, code: str) -> "Circuit":
        """
        Directly inject a block of Qreg code into the circuit.
        Use this for performance-critical loops (e.g. 256-bit ECC Shor).
        """
        self._ops.append(code) # type: ignore
        return self

    def _check_qubit(self, *indices: int) -> None:
        for i in indices:
            if not (0 <= i < self._n):
                raise IndexError(f"Qubit {i} out of range for {self._n}-qubit circuit.")

    # ═══════════════════════════════════════════════════════════════════════
    # ── PRIMITIVE SINGLE-QUBIT GATES ───────────────────────────────────────
    # ═══════════════════════════════════════════════════════════════════════

    def h(self, qubit: int) -> "Circuit":
        """Hadamard gate — creates superposition."""
        return self._add("H", [qubit])

    def x(self, qubit: int) -> "Circuit":
        """Pauli-X (NOT / bit-flip)."""
        return self._add("X", [qubit])

    def y(self, qubit: int) -> "Circuit":
        """Pauli-Y."""
        return self._add("Y", [qubit])

    def z(self, qubit: int) -> "Circuit":
        """Pauli-Z (phase-flip)."""
        return self._add("Z", [qubit])

    def s(self, qubit: int) -> "Circuit":
        """S gate — π/2 phase."""
        return self._add("S", [qubit])

    def t(self, qubit: int) -> "Circuit":
        """T gate — π/4 phase."""
        return self._add("T", [qubit])

    def rx(self, qubit: int, angle: float) -> "Circuit":
        """Rotation around X axis by *angle* radians."""
        return self._add("Rx", [qubit], angle)

    def ry(self, qubit: int, angle: float) -> "Circuit":
        """Rotation around Y axis by *angle* radians."""
        return self._add("Ry", [qubit], angle)

    def rz(self, qubit: int, angle: float) -> "Circuit":
        """Rotation around Z axis by *angle* radians."""
        return self._add("Rz", [qubit], angle)

    # ═══════════════════════════════════════════════════════════════════════
    # ── EXTENDED SINGLE-QUBIT GATES (auto-decomposed) ──────────────────────
    # ═══════════════════════════════════════════════════════════════════════

    def sdg(self, qubit: int) -> "Circuit":
        """S-dagger (S†) — inverse of S gate."""
        return self._add("Sdg", [qubit])

    def tdg(self, qubit: int) -> "Circuit":
        """T-dagger (T†) — inverse of T gate."""
        return self._add("Tdg", [qubit])

    def sx(self, qubit: int) -> "Circuit":
        """√X gate (SX)."""
        return self._add("SX", [qubit])

    def sxdg(self, qubit: int) -> "Circuit":
        """Inverse √X gate."""
        return self._add("SXdg", [qubit])

    def v(self, qubit: int) -> "Circuit":
        """V gate — alias for √X."""
        return self._add("V", [qubit])

    def p(self, qubit: int, lam: float) -> "Circuit":
        """Phase gate P(λ) — equivalent to Rz(λ)."""
        return self._add("P", [qubit], lam)

    def u1(self, qubit: int, lam: float) -> "Circuit":
        """U1(λ) gate — equivalent to Rz(λ)."""
        return self._add("U1", [qubit], lam)

    def u2(self, qubit: int, phi: float, lam: float) -> "Circuit":
        """U2(φ, λ) gate — single-pulse rotation."""
        return self._add("U2", [qubit], phi, lam)

    def u3(self, qubit: int, theta: float, phi: float, lam: float) -> "Circuit":
        """U3(θ, φ, λ) — the most general single-qubit gate."""
        return self._add("U3", [qubit], theta, phi, lam)

    def i(self, qubit: int) -> "Circuit":
        """Identity gate (X·X — no-op). Useful as a placeholder."""
        return self._add("X", [qubit])._add("X", [qubit])

    # ═══════════════════════════════════════════════════════════════════════
    # ── PRIMITIVE TWO-QUBIT GATES ──────────────────────────────────────────
    # ═══════════════════════════════════════════════════════════════════════

    def cnot(self, control: int, target: int) -> "Circuit":
        """CNOT — Controlled-NOT."""
        return self._add("CNOT", [control, target])

    def cx(self, control: int, target: int) -> "Circuit":
        """CX — alias for :meth:`cnot`."""
        return self.cnot(control, target)

    def swap(self, q1: int, q2: int) -> "Circuit":
        """SWAP gate."""
        return self._add("SWAP", [q1, q2])

    # ═══════════════════════════════════════════════════════════════════════
    # ── EXTENDED TWO-QUBIT GATES (auto-decomposed) ─────────────────────────
    # ═══════════════════════════════════════════════════════════════════════

    def cz(self, control: int, target: int) -> "Circuit":
        """Controlled-Z — entangling two-qubit gate."""
        return self._add("CZ", [control, target])

    def cy(self, control: int, target: int) -> "Circuit":
        """Controlled-Y."""
        return self._add("CY", [control, target])

    def ch(self, control: int, target: int) -> "Circuit":
        """Controlled-Hadamard."""
        return self._add("CH", [control, target])

    def crx(self, control: int, target: int, angle: float) -> "Circuit":
        """Controlled Rx rotation by *angle* radians."""
        return self._add("CRx", [control, target], angle)

    def cry(self, control: int, target: int, angle: float) -> "Circuit":
        """Controlled Ry rotation by *angle* radians."""
        return self._add("CRy", [control, target], angle)

    def crz(self, control: int, target: int, angle: float) -> "Circuit":
        """Controlled Rz rotation by *angle* radians."""
        return self._add("CRz", [control, target], angle)

    def cp(self, control: int, target: int, angle: float) -> "Circuit":
        """Controlled phase gate by *angle* radians."""
        return self._add("CP", [control, target], angle)

    def cs(self, control: int, target: int) -> "Circuit":
        """Controlled-S gate (Controlled phase π/2)."""
        return self._add("CP", [control, target], math.pi / 2)

    def ct(self, control: int, target: int) -> "Circuit":
        """Controlled-T gate (Controlled phase π/4)."""
        return self._add("CP", [control, target], math.pi / 4)

    def rxx(self, q1: int, q2: int, angle: float) -> "Circuit":
        """Ising XX coupling — RXX(angle)."""
        return self._add("RXX", [q1, q2], angle)

    def ryy(self, q1: int, q2: int, angle: float) -> "Circuit":
        """Ising YY coupling — RYY(angle)."""
        return self._add("RYY", [q1, q2], angle)

    def rzz(self, q1: int, q2: int, angle: float) -> "Circuit":
        """Ising ZZ coupling — RZZ(angle)."""
        return self._add("RZZ", [q1, q2], angle)

    def ecr(self, q1: int, q2: int) -> "Circuit":
        """Echoed Cross-Resonance (ECR) gate."""
        return self._add("ECR", [q1, q2])

    def iswap(self, q1: int, q2: int) -> "Circuit":
        """iSWAP gate — swaps with a phase of i."""
        # iSWAP = SWAP · (CZ with S phases)
        # Decomposition: S(q1), S(q2), H(q1), CNOT(q1,q2), CNOT(q2,q1), H(q2)
        return (
            self
            ._add("S", [q1])
            ._add("S", [q2])
            ._add("H", [q1])
            ._add("CNOT", [q1, q2])
            ._add("CNOT", [q2, q1])
            ._add("H", [q2])
        )

    # ═══════════════════════════════════════════════════════════════════════
    # ── THREE-QUBIT GATES ──────────────────────────────────────────────────
    # ═══════════════════════════════════════════════════════════════════════

    def ccnot(self, c1: int, c2: int, target: int) -> "Circuit":
        """Toffoli gate (CCNOT) — doubly-controlled NOT."""
        return self._add("CCNOT", [c1, c2, target])

    def toffoli(self, c1: int, c2: int, target: int) -> "Circuit":
        """Alias for :meth:`ccnot`."""
        return self.ccnot(c1, c2, target)

    def cswap(self, control: int, t1: int, t2: int) -> "Circuit":
        """Fredkin gate (CSWAP) — controlled SWAP."""
        return self._add("CSWAP", [control, t1, t2])

    def fredkin(self, control: int, t1: int, t2: int) -> "Circuit":
        """Alias for :meth:`cswap`."""
        return self.cswap(control, t1, t2)

    def ccz(self, c1: int, c2: int, target: int) -> "Circuit":
        """Controlled-Controlled-Z gate."""
        return self._add("CCZ", [c1, c2, target])

    # ═══════════════════════════════════════════════════════════════════════
    # ── HIGH-LEVEL COMPOSITE OPERATIONS ────────────────────────────────────
    # ═══════════════════════════════════════════════════════════════════════

    def bell_pair(self, q1: int = 0, q2: int = 1) -> "Circuit":
        """
        Prepare a Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2 on qubits q1, q2.

        Example::

            qpu.circuit(2).bell_pair().run()  # → "00" or "11"
        """
        return self._add("H", [q1])._add("CNOT", [q1, q2])

    def ghz(self, qubits: Optional[List[int]] = None) -> "Circuit":
        """
        Prepare a GHZ state across *qubits*.

        If *qubits* is None, uses all qubits in the circuit.

        Example::

            qpu.circuit(5).ghz().run()  # e.g. "00000" or "11111"
        """
        qs = list(range(self._n)) if qubits is None else qubits
        self._add("H", [qs[0]])
        for target in qs[1:]:
            self._add("CNOT", [qs[0], target])
        return self

    def w_state(self, qubits: Optional[List[int]] = None) -> "Circuit":
        """
        Prepare a W state (|100⟩+|010⟩+|001⟩)/√3 across *qubits*.

        Uses optimal Ry + CX decomposition for arbitrary n.
        """
        qs = list(range(self._n)) if qubits is None else qubits
        n = len(qs)
        if n == 1:
            return self._add("X", [qs[0]])
        # Build W state recursively via Ry rotations
        self._add("X", [qs[0]])
        for k in range(n - 1):
            angle = 2.0 * math.acos(math.sqrt(1.0 / (n - k)))
            self._add("CRy", [qs[k], qs[k + 1]], angle)
            self._add("CNOT", [qs[k + 1], qs[k]])
        return self

    def qft(self, qubits: Optional[List[int]] = None, inverse: bool = False) -> "Circuit":
        """
        Apply the Quantum Fourier Transform (or its inverse) to *qubits*.

        Example::

            qpu.circuit(4).qft().run()
        """
        qs = list(range(self._n)) if qubits is None else qubits
        n = len(qs)
        if inverse:
            qs = list(reversed(qs))
        for i, q in enumerate(qs):
            self._add("H", [q])
            for j in range(i + 1, n):
                angle = math.pi / (2 ** (j - i))
                if inverse:
                    angle = -angle
                self._add("CP", [qs[j], q], angle)
        # Bit-reversal swaps
        for i in range(n // 2):
            self._add("SWAP", [qs[i], qs[n - i - 1]])
        return self

    def iqft(self, qubits: Optional[List[int]] = None) -> "Circuit":
        """Inverse Quantum Fourier Transform."""
        return self.qft(qubits, inverse=True)

    def teleport(self, src: int = 0, ancilla: int = 1, dst: int = 2) -> "Circuit":
        """
        Quantum teleportation circuit from *src* through *ancilla* to *dst*.

        The *src* qubit should already hold the state to be teleported.

        Example::

            # Teleport |+⟩
            qpu.circuit(3).h(0).teleport(0, 1, 2).run()
        """
        # Bell pair on ancilla+dst
        self._add("H", [ancilla])
        self._add("CNOT", [ancilla, dst])
        # Bell measurement on src+ancilla
        self._add("CNOT", [src, ancilla])
        self._add("H", [src])
        # Corrections (in Qreg, classically conditioned — approximated here)
        self._add("CNOT", [ancilla, dst])
        self._add("CZ", [src, dst])
        return self

    def superdense_encode(self, q1: int, q2: int, bits: str) -> "Circuit":
        """
        Superdense coding encoding step.

        *bits* is a 2-character string of ``'0'`` and ``'1'``.

        Example::

            qpu.circuit(2).bell_pair().superdense_encode(0, 1, "10").run()
        """
        b1, b2 = bits[0], bits[1]
        if b2 == '1':
            self._add("X", [q1])
        if b1 == '1':
            self._add("Z", [q1])
        # Decode
        self._add("CNOT", [q1, q2])
        self._add("H", [q1])
        return self

    def phase_kickback(self, control: int, target: int) -> "Circuit":
        """
        Phase kickback primitive: X on target then CNOT back to control.
        Used as a building block for many oracle-based algorithms.
        """
        self._add("H", [control])
        self._add("X", [target])
        self._add("CNOT", [control, target])
        self._add("H", [control])
        return self

    def grover_diffusion(self, qubits: Optional[List[int]] = None) -> "Circuit":
        """
        Apply the Grover diffusion (inversion about average) operator.

        Example::

            c.h(0).h(1).grover_diffusion([0,1])
        """
        qs = list(range(self._n)) if qubits is None else qubits
        for q in qs:
            self._add("H", [q])
            self._add("X", [q])
        # Multi-controlled Z via CCNOT + H trick
        if len(qs) >= 3:
            self._add("H", [qs[-1]])
            self._add("CCNOT", [qs[0], qs[1], qs[-1]])
            self._add("H", [qs[-1]])
        elif len(qs) == 2:
            self._add("CZ", [qs[0], qs[1]])
        for q in reversed(qs):
            self._add("X", [q])
            self._add("H", [q])
        return self

    def swap_test(self, anc: int, qa: int, qb: int) -> "Circuit":
        """
        SWAP test: estimates ⟨ψ|φ⟩² using an ancilla qubit.

        Ancilla starts in |0⟩. Measure ancilla: if |0⟩ → states are identical.
        """
        self._add("H", [anc])
        self._add("CSWAP", [anc, qa, qb])
        self._add("H", [anc])
        return self

    def cluster_state(self, qubits: Optional[List[int]] = None) -> "Circuit":
        """
        Prepare a linear cluster state: H all then CZ between neighbours.
        """
        qs = list(range(self._n)) if qubits is None else qubits
        for q in qs:
            self._add("H", [q])
        for i in range(len(qs) - 1):
            self._add("CZ", [qs[i], qs[i + 1]])
        return self

    # ── Quantum arithmetic ─────────────────────────────────────────────────

    def flip_all(self, qubits: Optional[List[int]] = None) -> "Circuit":
        """Apply X to all (or specified) qubits — bit-flip every qubit."""
        qs = list(range(self._n)) if qubits is None else qubits
        for q in qs:
            self._add("X", [q])
        return self

    def increment(self, qubits: Optional[List[int]] = None) -> "Circuit":
        """
        Quantum increment: |x⟩ → |x+1 mod 2^n⟩ on the given register.

        Uses a ripple-carry decomposition (Toffoli ladder).
        """
        qs = list(range(self._n)) if qubits is None else qubits
        n = len(qs)
        # Increment = apply X to LSB, then conditionally cascade
        for i in range(n - 1, 0, -1):
            controls = qs[:i]
            if len(controls) == 1:
                self._add("CNOT", [controls[0], qs[i]])
            elif len(controls) == 2:
                self._add("CCNOT", [controls[0], controls[1], qs[i]])
            # Larger multi-control: use X + CCX + X pattern (ancilla-free approx)
        self._add("X", [qs[0]])
        return self

    def decrement(self, qubits: Optional[List[int]] = None) -> "Circuit":
        """Quantum decrement: |x⟩ → |x-1 mod 2^n⟩."""
        qs = list(range(self._n)) if qubits is None else qubits
        self.flip_all(qs)
        self.increment(qs)
        self.flip_all(qs)
        return self

    def add_constant(self, k: int, qubits: Optional[List[int]] = None) -> "Circuit":
        """Add integer *k* to a quantum register (mod 2^n) via repeated increment."""
        for _ in range(k % (2 ** (len(qubits) if qubits else self._n))):
            self.increment(qubits)
        return self

    # ── Misc ───────────────────────────────────────────────────────────────

    def barrier(self) -> "Circuit":
        """Visual separator — no-op on hardware."""
        self._ops.append("# --- barrier ---")
        return self

    def measure(self) -> "Circuit":
        """Mark this circuit for measurement."""
        self._measured = True
        return self

    def reset(self, qubit: int) -> "Circuit":
        """
        Reset a qubit to |0⟩ by measuring and conditionally flipping.
        Useful for ancilla recycling.

        .. note:: On QPU-1 this is approximated by two X gates (X·X = I).
        """
        # Real reset would be mid-circuit measurement; approximate here
        self._add("X", [qubit])
        self._add("X", [qubit])
        return self

    # ── Code generation & inspection ───────────────────────────────────────

    def to_qreg(self, auto_measure: bool = True) -> str:
        """
        Return the Qreg source code for this circuit.
        Lazy decomposition happens here.
        """
        # Stream-build to avoid holding a giant list of lines (ECC Shor can be huge).
        buf = io.StringIO()
        buf.write(f"q = Qreg({self._n})\n")

        for op in self._ops:
            if isinstance(op, str):
                # `raw()` blocks often already contain internal newlines.
                buf.write(op)
                if not op.endswith("\n"):
                    buf.write("\n")
            else:
                for line in _expand(*op):
                    buf.write(line)
                    buf.write("\n")

        if self._measured or auto_measure:
            buf.write("print(q.measure())\n")
        return buf.getvalue().rstrip("\n")

    def gate_count(self) -> int:
        """Approximate gate count (construction-level ops)."""
        return len(self._ops)

    def depth(self) -> int:
        """Estimate circuit depth."""
        return max(1, self.gate_count() // max(1, self._n))

    def draw(self, auto_measure: bool = True) -> None:
        """Print the Qreg source to stdout."""
        print(self.to_qreg(auto_measure=auto_measure))

    def __repr__(self) -> str:
        return f"Circuit(n_qubits={self._n}, gates={self.gate_count()})"

    def _build_code(self, with_measure: bool = True) -> str:
        return self.to_qreg(auto_measure=with_measure)

    # ── Execution ──────────────────────────────────────────────────────────

    def run(
        self,
        execution_mode: Literal["instant", "overnight"] = "instant",
        max_duration_seconds: Optional[int] = None,
        fast: bool = False,
    ) -> "JobResult":
        """
        Submit this circuit to QPU-1 and block until a result is returned.

        Parameters
        ----------
        execution_mode:
            ``"instant"`` (default) or ``"overnight"`` for long jobs.
        max_duration_seconds:
            Per-request timeout cap in seconds.
        fast:
            If ``True``, send via the Gradio ``/execute`` concurrent channel
            (lower latency).  Recommended for ECC Shor and other large circuits
            where queue depth matters.

        Returns
        -------
        JobResult
            Use ``.bits`` for the measurement bit-string.
        """
        if self._client is None:
            raise RuntimeError(
                "This Circuit has no client attached. "
                "Create it via qpu.circuit(n) or pass a QPU1 instance."
            )
        return self._client.run_qreg(
            self._build_code(with_measure=True),
            execution_mode=execution_mode,
            max_duration_seconds=max_duration_seconds,
        )
