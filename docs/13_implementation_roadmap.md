# 13 — Implementation Roadmap

## 13.1 Development Phases

### Phase 1: Classical Infrastructure (Weeks 1-4)

**Objective:** Build and test all classical components.

| Task | Description | Deliverable |
|---|---|---|
| 1.1 | Modular arithmetic library (F_p) | Tested library with add, sub, mul, inv, sqrt |
| 1.2 | EC point operations (affine + Jacobian) | Point add, double, scalar mult, conversion |
| 1.3 | Table generation | 16,384-entry precomputed table generator |
| 1.4 | Key recovery module | Post-processing: c⁻¹ mod n, verification |
| 1.5 | End-to-end classical test | Known-key recovery on secp256k1 |

**Testing:** Compare against reference implementations (OpenSSL, libsecp256k1).

### Phase 2: Quantum Circuit Primitives (Weeks 5-10)

**Objective:** Implement and verify basic quantum arithmetic circuits.

| Task | Description | Deliverable |
|---|---|---|
| 2.1 | Ripple-carry adder (256-bit) | Reversible adder circuit |
| 2.2 | Comparator circuit | Reversible ≥ comparator |
| 2.3 | ModAdd / ModSub circuits | Verified modular arithmetic |
| 2.4 | Schoolbook multiplier (128-bit) | Building block for Karatsuba |
| 2.5 | Karatsuba multiplier (256-bit) | 3-way decomposed multiplier |
| 2.6 | Modular reduction (special p) | Exploiting p = 2²⁵⁶ − c |
| 2.7 | Full ModMul circuit | Multiplication + reduction + Bennett |

**Verification:** Simulate each circuit on 8/16/32-bit versions and compare outputs to classical computation for all 2^{2n} input pairs (exhaustive for small n).

### Phase 3: EC Operations (Weeks 11-16)

**Objective:** Build elliptic curve point operations from modular arithmetic.

| Task | Description | Deliverable |
|---|---|---|
| 3.1 | Point doubling circuit (Jacobian) | Reversible doubling |
| 3.2 | Mixed point addition circuit | Jacobian + affine → Jacobian |
| 3.3 | Special case handling | Identity, equality, negation detection |
| 3.4 | Controlled point addition | Control-qubit gated addition |
| 3.5 | Point negation circuit | Y → p − Y |

**Verification:** Simulate on a small curve (e.g., y² = x³ + 7 over F_p for p = 67, n = 79) and verify all point operations.

### Phase 4: QROM and Windowed Arithmetic (Weeks 17-22)

**Objective:** Implement the windowed scalar multiplication.

| Task | Description | Deliverable |
|---|---|---|
| 4.1 | QROM (unary iteration, 256 entries) | Parameterized QROM circuit |
| 4.2 | QROM uncomputation | Reverse QROM circuit |
| 4.3 | Single-window iteration | QROM + PointAdd + QROM⁻¹ |
| 4.4 | Checkpoint management | Pebble-game style checkpointing |
| 4.5 | Full windowed scalar mult | 64-window loop with checkpoints |

**Verification:** Simulate on toy curve (16-bit) with full windowed scalar multiplication.

### Phase 5: Full Circuit Assembly (Weeks 23-28)

**Objective:** Assemble the complete ECDLP solver circuit.

| Task | Description | Deliverable |
|---|---|---|
| 5.1 | QFT circuit (256-bit) | Approximate QFT with rotation synthesis |
| 5.2 | Circuit initialization | Hadamard layer, register initialization |
| 5.3 | Full oracle (forward) | Windowed scalar mult + accumulator |
| 5.4 | Circuit integration | Init → Oracle → QFT → Measure |
| 5.5 | Gate count verification | Automated counter matching ~79M |
| 5.6 | Qubit count verification | Automated counter matching ~6,004 |

### Phase 6: Error Correction Integration (Weeks 29-36)

**Objective:** Map logical circuit to surface code implementation.

| Task | Description | Deliverable |
|---|---|---|
| 6.1 | Logical-to-physical qubit mapping | Surface code patch layout |
| 6.2 | T-gate decomposition | Toffoli → Clifford + T |
| 6.3 | Magic state factory design | 15-to-1 distillation layout |
| 6.4 | Lattice surgery scheduling | CNOT/Toffoli execution timeline |
| 6.5 | Runtime estimation | Physical runtime calculation |
| 6.6 | Error budget verification | End-to-end error probability |

### Phase 7: Validation & Documentation (Weeks 37-42)

**Objective:** Comprehensive testing and documentation.

| Task | Description | Deliverable |
|---|---|---|
| 7.1 | Small-curve end-to-end test | Full algorithm on 16/32-bit curves |
| 7.2 | Gate count audit | Independent verification of counts |
| 7.3 | Formal correctness review | Mathematical proof review |
| 7.4 | Documentation finalization | All 15 chapters complete |
| 7.5 | Reproducibility package | All code, tests, and scripts |

## 13.2 Testing Strategy

### 13.2.1 Unit Testing

Every sub-circuit is tested independently:

```
Test(ModAdd, n=8):
  For all a, b ∈ [0, p_8-1]:
    assert circuit_output(a, b) == (a + b) % p_8
    assert ancillae_clean(circuit)
```

### 13.2.2 Scaled Testing

Full algorithm tested at multiple scales:

| Scale | Field bits | Qubits | Gates | Simulation method |
|---|---|---|---|---|
| Toy | 4 | ~60 | ~500 | State vector |
| Small | 8 | ~120 | ~5K | State vector |
| Medium | 16 | ~250 | ~200K | State vector (GPU) |
| Large | 32 | ~500 | ~5M | Tensor network |
| Target | 256 | ~6,000 | ~79M | Resource count only |

### 13.2.3 Property-Based Testing

```
For random inputs a, b:
  1. ModMul(a, b) == a * b mod p                    (functional correctness)
  2. ModMul(a, b) == ModMul(b, a)                    (commutativity)
  3. ModMul(ModMul(a, b), c) == ModMul(a, ModMul(b, c))  (associativity)
  4. ancilla_state == |0⟩^k after computation        (clean uncomputation)
```

### 13.2.4 Regression Testing

After any circuit optimization, re-run all unit and integration tests to ensure correctness is preserved.

## 13.3 Simulation Tools

| Tool | Purpose | Scale |
|---|---|---|
| Qiskit (IBM) | Circuit construction, small simulation | ≤ 30 qubits |
| Cirq (Google) | Circuit construction, noise simulation | ≤ 30 qubits |
| QuEST | State vector simulation | ≤ 40 qubits (GPU) |
| Stim | Clifford circuit simulation | Any size (Clifford only) |
| Custom simulator | Modular arithmetic verification | Up to 32-bit fields |
| Resource counter | Gate/qubit counting | Full 256-bit circuit |

## 13.4 Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Gate count exceeds 79M | Medium | Must re-optimize | Multiple optimization strategies ready |
| Qubit count exceeds 6,000 | Medium | Need different pebbling | Reduce checkpoints (trade time for space) |
| Special case bug | Low | Incorrect results | Exhaustive testing on small curves |
| QROM error | Low | Wrong table lookup | Bit-level verification |
| QFT approximation | Very low | Slight success degradation | Conservative rotation synthesis |

## 13.5 Milestones

| Milestone | Week | Criterion |
|---|---|---|
| M1: Classical library complete | 4 | All tests pass, matches libsecp256k1 |
| M2: Modular arithmetic circuits | 10 | Exhaustive test on 8-bit field |
| M3: EC operations verified | 16 | Full point arithmetic on toy curve |
| M4: Windowed scalar mult works | 22 | End-to-end on 16-bit curve (simulated) |
| M5: Full circuit assembled | 28 | Gate count = 79M ± 5%, qubit count = 6,004 |
| M6: Error correction designed | 36 | Physical resource estimate complete |
| M7: Project complete | 42 | All documentation and tests finalized |

## 13.6 Team Structure

| Role | Count | Responsibilities |
|---|---|---|
| Quantum Algorithm Lead | 1 | Algorithm design, correctness proofs |
| Quantum Circuit Engineers | 3 | Circuit implementation, optimization |
| Classical Software Engineers | 2 | Pre/post-processing, testing infrastructure |
| QEC Specialist | 1 | Surface code design, error analysis |
| Verification Engineer | 1 | Testing, formal verification |
| Technical Writer | 1 | Documentation |
| **Total** | **9** | |
