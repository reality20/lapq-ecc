"""
Quantum ECDLP Solver for secp256k1

A mathematically correct quantum solver for the Elliptic Curve Discrete Logarithm Problem (ECDLP)
on the secp256k1 curve using Shor's algorithm with windowed arithmetic.

This package implements the full design targeting:
- ~6,000 logical qubits
- ~79 × 10⁶ gates (T + Clifford)
- Window size w=4 with combined addressing
"""

__version__ = "1.0.0"
__author__ = "ECDLP Solver Team"

from .classical.field import Fp, Fp256
from .classical.curve import ECPoint, secp256k1_generator, secp256k1_order
from .classical.tables import generate_qrom_tables
from .classical.postprocess import recover_private_key

from .quantum.primitives.adder import RippleCarryAdder, ModAdd
from .quantum.primitives.comparator import Comparator
from .quantum.primitives.multiplier import Multiplier, KaratsubaMultiplier
from .quantum.primitives.cswap import CSWAP

from .quantum.arithmetic.mod_add import ModularAdder
from .quantum.arithmetic.mod_mul import ModularMultiplier
from .quantum.arithmetic.mod_reduce import ModularReducer
from .quantum.arithmetic.mod_sub import ModularSubtractor

from .quantum.ec.point_double import PointDoubler
from .quantum.ec.point_add import MixedPointAdder
from .quantum.ec.point_negate import PointNegator
from .quantum.ec.ctrl_point_add import ControlledPointAdder

from .quantum.memory.qrom import QROM
from .quantum.transform.qft import QFT

from .quantum.top.scalar_mult import WindowedScalarMult
from .quantum.top.oracle import Oracle
from .quantum.top.ecdlp_solver import ECDLPSolver

from .verification.gate_counter import GateCounter
from .verification.qubit_counter import QubitTracker
from .verification.depth_analyzer import DepthAnalyzer

from .error_correction.surface_code import SurfaceCodeEstimator

__all__ = [
    # Classical components
    "Fp", "Fp256", "ECPoint", "secp256k1_generator", "secp256k1_order",
    "generate_qrom_tables", "recover_private_key",
    
    # Quantum primitives
    "RippleCarryAdder", "ModAdd", "Comparator", "Multiplier", 
    "KaratsubaMultiplier", "CSWAP",
    
    # Quantum arithmetic
    "ModularAdder", "ModularMultiplier", "ModularReducer", "ModularSubtractor",
    
    # Quantum EC operations
    "PointDoubler", "MixedPointAdder", "PointNegator", "ControlledPointAdder",
    
    # Quantum memory and transforms
    "QROM", "QFT",
    
    # Top-level components
    "WindowedScalarMult", "Oracle", "ECDLPSolver",
    
    # Verification
    "GateCounter", "QubitTracker", "DepthAnalyzer",
    
    # Error correction
    "SurfaceCodeEstimator",
]
