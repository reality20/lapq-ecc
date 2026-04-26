"""
Elliptic curve point operations for secp256k1.

Curve equation: y² = x³ + 7 (over F_p)
"""

from typing import Optional, Tuple
from .field import Fp


class ECPoint:
    """Point on secp256k1 in affine coordinates."""
    
    # Curve parameter: y² = x³ + 7
    B = 7
    
    def __init__(self, x: int, y: int, infinity: bool = False):
        self.infinity = infinity
        if infinity:
            self.x = 0
            self.y = 0
        else:
            self.x = Fp(x)
            self.y = Fp(y)
    
    @staticmethod
    def identity() -> 'ECPoint':
        """Return the point at infinity (identity element)."""
        return ECPoint(0, 0, infinity=True)
    
    def is_identity(self) -> bool:
        return self.infinity
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ECPoint):
            return False
        if self.infinity and other.infinity:
            return True
        if self.infinity or other.infinity:
            return False
        return self.x == other.x and self.y == other.y
    
    def __repr__(self) -> str:
        if self.infinity:
            return "ECPoint(O)"
        return f"ECPoint(x={hex(int(self.x))}, y={hex(int(self.y))})"
    
    def __add__(self, other: 'ECPoint') -> 'ECPoint':
        """Add two points using affine coordinates."""
        if self.infinity:
            return other
        if other.infinity:
            return self
        
        # Check if P = -Q (result is identity)
        if self.x == other.x:
            if self.y == other.y:
                # Same point, use doubling
                return self.double()
            else:
                # P = -Q, result is identity
                return ECPoint.identity()
        
        # Standard point addition formula
        lam = (other.y - self.y) * (other.x - self.x).inv()
        x3 = lam * lam - self.x - other.x
        y3 = lam * (self.x - x3) - self.y
        return ECPoint(int(x3), int(y3))
    
    def __neg__(self) -> 'ECPoint':
        """Negate a point: -(x, y) = (x, -y)."""
        if self.infinity:
            return self
        return ECPoint(int(self.x), int(Fp.P - self.y.v))
    
    def double(self) -> 'ECPoint':
        """Double a point using tangent line."""
        if self.infinity or self.y.v == 0:
            return ECPoint.identity()
        
        # λ = (3x²) / (2y) for secp256k1 (a=0)
        three_x2 = Fp(3) * self.x * self.x
        two_y = Fp(2) * self.y
        lam = three_x2 * two_y.inv()
        
        x3 = lam * lam - Fp(2) * self.x
        y3 = lam * (self.x - x3) - self.y
        return ECPoint(int(x3), int(y3))
    
    def scalar_mult(self, k: int) -> 'ECPoint':
        """Scalar multiplication using double-and-add algorithm."""
        if k == 0 or self.infinity:
            return ECPoint.identity()
        
        result = ECPoint.identity()
        addend = self
        
        while k > 0:
            if k & 1:
                result = result + addend
            addend = addend.double()
            k >>= 1
        
        return result
    
    def to_jacobian(self) -> 'JacobianPoint':
        """Convert to Jacobian projective coordinates."""
        if self.infinity:
            return JacobianPoint(1, 1, 0, infinity=True)
        return JacobianPoint(int(self.x), int(self.y), 1)
    
    @classmethod
    def from_jacobian(cls, jp: 'JacobianPoint') -> 'ECPoint':
        """Convert from Jacobian projective coordinates."""
        if jp.infinity or jp.z.v == 0:
            return cls.identity()
        
        z_inv = jp.z.inv()
        z_inv2 = z_inv.square()
        z_inv3 = z_inv2 * z_inv
        
        x = jp.x * z_inv2
        y = jp.y * z_inv3
        
        return cls(int(x), int(y))


class JacobianPoint:
    """Point in Jacobian projective coordinates (X : Y : Z)."""
    
    def __init__(self, x: int, y: int, z: int, infinity: bool = False):
        self.infinity = infinity
        self.x = Fp(x)
        self.y = Fp(y)
        self.z = Fp(z)
    
    def is_identity(self) -> bool:
        return self.infinity or self.z.v == 0
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, JacobianPoint):
            return False
        if self.is_identity() and other.is_identity():
            return True
        if self.is_identity() or other.is_identity():
            return False
        
        # Compare in affine coordinates
        z1_inv2 = self.z.inv().square()
        z1_inv3 = z1_inv2 * self.z.inv()
        z2_inv2 = other.z.inv().square()
        z2_inv3 = z2_inv2 * other.z.inv()
        
        x1_affine = self.x * z1_inv2
        y1_affine = self.y * z1_inv3
        x2_affine = other.x * z2_inv2
        y2_affine = other.y * z2_inv3
        
        return x1_affine == x2_affine and y1_affine == y2_affine
    
    def __repr__(self) -> str:
        if self.is_identity():
            return "JacobianPoint(O)"
        return f"JacobianPoint(X={hex(int(self.x))}, Y={hex(int(self.y))}, Z={hex(int(self.z))})"
    
    def to_affine(self) -> ECPoint:
        """Convert to affine coordinates."""
        return ECPoint.from_jacobian(self)


# secp256k1 generator point G
G_X = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
G_Y = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def secp256k1_generator() -> ECPoint:
    """Return the secp256k1 generator point G."""
    return ECPoint(G_X, G_Y)


# Group order n
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def secp256k1_order() -> int:
    """Return the group order of secp256k1."""
    return N
