"""
QROM table generation for windowed scalar multiplication.

Generates precomputed point tables for the combined window approach:
T[j][(i,k)] = i · 2^(4j) · P + k · 2^(4j) · Q
"""

from typing import Dict, List, Tuple
from .curve import ECPoint


def generate_qrom_tables(
    P: ECPoint, 
    Q: ECPoint, 
    window_size: int = 4,
    num_bits: int = 256
) -> List[Dict[Tuple[int, int], ECPoint]]:
    """
    Generate precomputed point tables for QROM lookups.
    
    For the combined window approach with window_size=4:
    - Each window processes 4 bits from scalar a and 4 bits from scalar b
    - Combined address is 8 bits (256 possible values)
    - Total windows: 256 / 4 = 64
    
    Args:
        P: Generator point (classical)
        Q: Target point (classical, public key)
        window_size: Bits per window (default 4)
        num_bits: Total bits in scalars (default 256)
    
    Returns:
        List of 64 dictionaries, each mapping (i, k) tuples to ECPoints.
        Each dictionary has 256 entries (16 × 16).
    """
    w = window_size
    num_windows = num_bits // w  # 64 for w=4
    
    # Step 1: Compute powers of 2^w for both P and Q
    # P_powers[j] = [2^(wj)] · P
    # Q_powers[j] = [2^(wj)] · Q
    P_powers: List[ECPoint] = []
    Q_powers: List[ECPoint] = []
    
    current_P = P
    current_Q = Q
    
    for j in range(num_windows):
        P_powers.append(current_P)
        Q_powers.append(current_Q)
        
        # Advance by 2^w = 16 doublings
        for _ in range(w):
            current_P = current_P.double()
            current_Q = current_Q.double()
    
    # Step 2: Generate combined tables for each window
    tables: List[Dict[Tuple[int, int], ECPoint]] = []
    
    for j in range(num_windows):
        table_j: Dict[Tuple[int, int], ECPoint] = {}
        
        # Precompute multiples of P_powers[j]: iP for i ∈ {0, ..., 15}
        iP: List[ECPoint] = [ECPoint.identity()]
        for i in range(1, 2**w):
            iP.append(iP[-1] + P_powers[j])
        
        # Precompute multiples of Q_powers[j]: kQ for k ∈ {0, ..., 15}
        kQ: List[ECPoint] = [ECPoint.identity()]
        for k in range(1, 2**w):
            kQ.append(kQ[-1] + Q_powers[j])
        
        # Combined table: T[j][(i,k)] = iP[i] + kQ[k]
        for i in range(2**w):
            for k in range(2**w):
                table_j[(i, k)] = iP[i] + kQ[k]
        
        tables.append(table_j)
    
    return tables


def encode_point_for_qrom(point: ECPoint, bits: int = 256) -> list[int]:
    """
    Encode an EC point as a bit string for QROM.
    
    Returns a list of 2*bits integers (0 or 1) representing
    the x and y coordinates in little-endian order.
    
    Format: [x_0, x_1, ..., x_{bits-1}, y_0, y_1, ..., y_{bits-1}]
    """
    if point.is_identity():
        return [0] * (2 * bits)
    
    # Convert coordinates to little-endian bits
    x_bits = []
    y_bits = []
    
    x_val = int(point.x)
    y_val = int(point.y)
    
    for _ in range(bits):
        x_bits.append(x_val & 1)
        y_bits.append(y_val & 1)
        x_val >>= 1
        y_val >>= 1
    
    return x_bits + y_bits


def decode_point_from_qrom(bit_string: list[int], bits: int = 256) -> ECPoint:
    """
    Decode a bit string back to an EC point.
    
    Inverse of encode_point_for_qrom.
    """
    if all(b == 0 for b in bit_string):
        return ECPoint.identity()
    
    x_bits = bit_string[:bits]
    y_bits = bit_string[bits:]
    
    x_val = sum(b << i for i, b in enumerate(x_bits))
    y_val = sum(b << i for i, b in enumerate(y_bits))
    
    return ECPoint(x_val, y_val)
