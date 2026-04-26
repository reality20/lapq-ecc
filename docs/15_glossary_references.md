# 15 — Glossary & References

## 15.1 Glossary

### A

**Affine Coordinates:** Representation of an elliptic curve point as (x, y) satisfying the curve equation directly. Simple but requires field inversion for point addition.

**Ancilla Qubit:** A qubit initialized to |0⟩ used as temporary workspace in a quantum computation. Must be returned to |0⟩ (uncomputed) before the end of the circuit to avoid entanglement with the output.

### B

**Bennett's Trick:** A technique for making irreversible computations reversible by computing the result, copying it, and then uncomputing the intermediate garbage. Introduced by Charles Bennett (1973).

### C

**CNOT (Controlled-NOT):** A two-qubit gate that flips the target qubit if and only if the control qubit is |1⟩. Fundamental building block of quantum circuits.

**Code Distance (d):** In a quantum error-correcting code, the minimum weight of a non-trivial logical operator. Determines the number of errors the code can correct: ⌊(d−1)/2⌋.

**Coset Representation:** Storing field elements in the range [0, 2p−1] instead of [0, p−1], deferring modular reduction to save gates.

### E

**ECDLP (Elliptic Curve Discrete Logarithm Problem):** Given points P and Q = kP on an elliptic curve, find the integer k. The fundamental hard problem underlying elliptic curve cryptography.

**ECDSA (Elliptic Curve Digital Signature Algorithm):** A digital signature scheme based on the hardness of ECDLP. Used in Bitcoin, Ethereum, and many other systems.

### F

**F_p (Prime Field):** The finite field of integers modulo a prime p, with arithmetic operations (add, multiply, inverse) all performed modulo p.

### H

**Hadamard Gate (H):** A single-qubit gate that maps |0⟩ → |+⟩ = (|0⟩+|1⟩)/√2 and |1⟩ → |−⟩ = (|0⟩−|1⟩)/√2. Creates uniform superposition.

**Hidden Subgroup Problem (HSP):** Given a function f on a group G that is constant on cosets of an unknown subgroup H, find H. Shor's algorithm solves the abelian HSP efficiently.

### J

**Jacobian Coordinates:** Projective representation (X : Y : Z) of an elliptic curve point corresponding to affine point (X/Z², Y/Z³). Eliminates field inversions from point arithmetic.

### K

**Karatsuba Multiplication:** A divide-and-conquer algorithm for integer multiplication. Splits n-bit numbers into two halves and uses 3 multiplications of n/2-bit numbers instead of 4, giving O(n^{1.585}) complexity.

### L

**Lattice Surgery:** A method for performing logical gates in the surface code by merging and splitting code patches. The primary mechanism for logical CNOT and multi-qubit gates.

**Logical Qubit:** An error-corrected qubit encoded in many physical qubits. Provides much lower error rates than any individual physical qubit.

### M

**Magic State Distillation:** A protocol for producing high-fidelity T-states from many noisy T-states. Required because T-gates cannot be implemented transversally in the surface code.

**Mixed Addition:** Point addition where one input is in Jacobian coordinates and the other in affine coordinates. Saves ~4 field multiplications compared to full Jacobian-Jacobian addition.

**Montgomery Multiplication:** A method for modular multiplication that replaces division by the modulus with division by a power of 2 (which is free in binary). Requires elements to be stored in Montgomery form.

### P

**Pebble Game:** A strategy for managing space in reversible computation. Uses a limited number of "pebbles" (stored checkpoints) to enable uncomputation without storing all intermediate results.

**Physical Qubit:** A single quantum two-level system (e.g., a superconducting transmon). Many physical qubits encode one logical qubit via error correction.

### Q

**QFT (Quantum Fourier Transform):** The quantum analogue of the discrete Fourier transform. Maps computational basis states to frequency basis states. Central to Shor's algorithm.

**QROM (Quantum Read-Only Memory):** A quantum circuit that loads classical data indexed by a quantum address: |i⟩|0⟩ → |i⟩|data[i]⟩. Implemented via controlled gates.

### R

**Ripple-Carry Adder:** A quantum circuit for binary addition where carries propagate sequentially from least significant to most significant bit. O(n) depth for n-bit addition.

### S

**secp256k1:** An elliptic curve defined by the Standards for Efficient Cryptography (SEC). Equation: y² = x³ + 7 over a 256-bit prime field. Used by Bitcoin and Ethereum.

**Shor's Algorithm:** A quantum algorithm that solves the integer factoring and discrete logarithm problems in polynomial time. For ECDLP on an n-bit curve, requires O(n) qubits and O(n³) gates.

**Surface Code:** A topological quantum error-correcting code defined on a 2D grid of qubits. Has a high error threshold (~1%) and requires only nearest-neighbor qubit interactions.

### T

**T Gate:** A single-qubit phase gate: T = diag(1, e^{iπ/4}). The "expensive" gate in fault-tolerant quantum computing, requiring magic state distillation.

**Toffoli Gate (CCX):** A three-qubit gate that flips the target if both controls are |1⟩. Universal for classical reversible computation. Decomposes into 7 T-gates in the surface code.

### U

**Unary Iteration:** A technique for implementing QROM where the binary address is first decoded into a one-hot (unary) representation, enabling efficient data loading with single-controlled gates.

**Uncomputation:** Running a quantum computation in reverse to return ancilla qubits to |0⟩. Essential for maintaining reversibility and avoiding unwanted entanglement.

### W

**Windowed Arithmetic:** Processing multiple bits of a scalar simultaneously in scalar multiplication, reducing the number of group operations at the cost of precomputation and lookup tables.

---

## 15.2 References

### Foundational Papers

1. **P. W. Shor.** "Polynomial-Time Algorithms for Prime Factorization and Discrete Logarithms on a Quantum Computer." *SIAM Journal on Computing*, 26(5):1484–1509, 1997. — The original algorithm.

2. **J. Proos and C. Zalka.** "Shor's Discrete Logarithm Quantum Algorithm for Elliptic Curves." *Quantum Information & Computation*, 3(4):317–344, 2003. — Adapts Shor's algorithm specifically to ECDLP.

3. **M. Roetteler, M. Naehrig, K. M. Svore, and K. Lauter.** "Quantum Resource Estimates for Computing Elliptic Curve Discrete Logarithms." *ASIACRYPT 2017*, LNCS 10625, pp. 241–270, 2017. — Detailed quantum resource estimates for ECDLP.

### Quantum Arithmetic

4. **S. A. Cuccaro, T. G. Draper, S. A. Kutin, and D. P. Moulton.** "A New Quantum Ripple-Carry Addition Circuit." *arXiv:quant-ph/0410184*, 2004. — The Cuccaro adder used in our design.

5. **T. Häner, S. Jaques, M. Naehrig, M. Roetteler, and M. Naehrig.** "Improved Quantum Circuits for Elliptic Curve Discrete Logarithms." *PQCrypto 2020*, LNCS 12100, pp. 425–444, 2020. — Improved arithmetic circuits.

6. **C. Gidney.** "Halving the Cost of Quantum Addition." *Quantum*, 2:74, 2018. — Optimized quantum addition circuits.

### Error Correction

7. **A. G. Fowler, M. Mariantoni, J. M. Martinis, and A. N. Cleland.** "Surface Codes: Towards Practical Large-Scale Quantum Computation." *Physical Review A*, 86(3):032324, 2012. — Comprehensive surface code reference.

8. **D. Litinski.** "A Game of Surface Codes: Large-Scale Quantum Computing with Lattice Surgery." *Quantum*, 3:128, 2019. — Lattice surgery compilation for surface codes.

9. **C. Gidney and M. Ekerå.** "How to Factor 2048-bit RSA Integers in 8 Hours Using 20 Million Noisy Qubits." *Quantum*, 5:433, 2021. — State-of-the-art resource estimation techniques.

### QROM and Windowed Arithmetic

10. **C. Gidney and M. Ekerå.** "Windowed Quantum Arithmetic." *arXiv:1905.07682*, 2019. — Windowed exponentiation techniques for quantum circuits.

11. **V. Kliuchnikov, D. Maslov, and M. Mosca.** "Asymptotically Optimal Approximation of Single Qubit Unitaries by Clifford and T Circuits." *Physical Review Letters*, 110(19):190502, 2013. — Rotation synthesis for QFT.

### Reversible Computation

12. **C. H. Bennett.** "Logical Reversibility of Computation." *IBM Journal of Research and Development*, 17(6):525–532, 1973. — Bennett's reversible computation trick.

13. **R. Y. Levine and A. T. Sherman.** "A Note on Bennett's Time-Space Tradeoff for Reversible Computation." *SIAM Journal on Computing*, 19(4):673–677, 1990. — Pebble game analysis.

### secp256k1 Specification

14. **Certicom Research.** "SEC 2: Recommended Elliptic Curve Domain Parameters." *Standards for Efficient Cryptography*, Version 2.0, 2010. — Official secp256k1 specification.

### Recent Resource Estimates

15. **M. Webber et al.** "The Impact of Hardware Specifications on Reaching Quantum Advantage in the Fault Tolerant Regime." *AVS Quantum Science*, 4(1):013801, 2022. — Physical resource estimates for cryptographically relevant quantum computing.

16. **S. Jaques and A. Schanck.** "Quantum Cryptanalysis in the RAM Model: Claw-Finding Attacks on SIKE." *CRYPTO 2019*, pp. 32–61. — Quantum memory models.

---

## 15.3 Constants Reference

### secp256k1 Parameters (Hexadecimal)

```
p  = FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
n  = FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
a  = 0
b  = 7
h  = 1
```

### secp256k1 Parameters (Decimal)

```
p  = 115792089237316195423570985008687907853269984665640564039457584007908834671663
n  = 115792089237316195423570985008687907852837564279074904382605163141518161494337
c  = p - 2^256 = -4294968273 (mod 2^256)
   = 4294968273 (unsigned)
```

### Derived Constants

```
2^256 mod p = 4294968273 = c
p + 1 = 2^256 - 4294968272
(p - 1) / 2 = 57896044618658097711785492504343953926634992332820282019728792003954417335831
```

### Circuit Constants

```
Field bits:     n = 256
Window size:    w = 4
Combined window: 2w = 8
Windows per scalar: 256/4 = 64
QROM entries per window: 2^8 = 256
Total table entries: 64 × 256 = 16,384
Points per entry: 1 (affine, 512 bits)
```
