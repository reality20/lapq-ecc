"""
Classical post-processing for key recovery.

After quantum measurement, recover the private key k from (c, d).
"""

from typing import Optional
from .curve import ECPoint, secp256k1_order


def recover_private_key(
    c: int, 
    d: int, 
    n: Optional[int] = None,
    P: Optional[ECPoint] = None,
    Q: Optional[ECPoint] = None,
    verify: bool = True
) -> Optional[int]:
    """
    Recover the private key from Shor's algorithm measurement results.
    
    Given measurement outcomes (c, d) satisfying ck + d ≡ 0 (mod n),
    compute k = -d · c^(-1) mod n.
    
    Args:
        c: Measurement result from register a
        d: Measurement result from register b
        n: Group order (default: secp256k1 order)
        P: Generator point (for verification)
        Q: Target public key (for verification)
        verify: Whether to verify the recovered key
    
    Returns:
        The private key k if successful and verified, None otherwise.
    
    Raises:
        ValueError: If c = 0 (need to re-run quantum circuit)
    """
    if n is None:
        n = secp256k1_order()
    
    if c == 0:
        raise ValueError("c = 0: need to re-run quantum circuit")
    
    # Compute modular inverse using extended Euclidean algorithm
    c_inv = pow(c, n - 2, n)  # Fermat's little theorem (n is prime)
    
    # Compute k = -d * c^(-1) mod n
    k = (-d * c_inv) % n
    
    # Verify if requested and points provided
    if verify and P is not None and Q is not None:
        computed_Q = P.scalar_mult(k)
        if computed_Q != Q:
            return None  # Verification failed
    
    return k


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """
    Extended Euclidean algorithm.
    
    Returns (gcd, x, y) such that ax + by = gcd.
    """
    if a == 0:
        return b, 0, 1
    
    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    
    return gcd, x, y


def modular_inverse(a: int, n: int) -> int:
    """
    Compute modular inverse using extended GCD.
    
    Returns x such that ax ≡ 1 (mod n).
    """
    gcd, x, _ = extended_gcd(a % n, n)
    if gcd != 1:
        raise ValueError(f"Modular inverse does not exist for {a} mod {n}")
    return (x % n + n) % n


def verify_key(k: int, P: ECPoint, Q: ECPoint) -> bool:
    """
    Verify that kP = Q.
    
    Args:
        k: Candidate private key
        P: Generator point
        Q: Public key
    
    Returns:
        True if kP = Q, False otherwise.
    """
    computed = P.scalar_mult(k)
    return computed == Q
