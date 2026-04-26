"""
Finite field arithmetic over F_p for secp256k1.

The secp256k1 prime: p = 2^256 - 4294968273
"""

from typing import Union


class Fp:
    """Field element in F_p for secp256k1."""
    
    # secp256k1 prime: p = 2^256 - 4294968273
    P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    
    def __init__(self, value: Union[int, 'Fp']):
        if isinstance(value, Fp):
            self.v = value.v
        else:
            self.v = value % self.P
    
    def __add__(self, other: 'Fp') -> 'Fp':
        return Fp(self.v + other.v)
    
    def __sub__(self, other: 'Fp') -> 'Fp':
        return Fp(self.v - other.v)
    
    def __mul__(self, other: 'Fp') -> 'Fp':
        return Fp(self.v * other.v)
    
    def __neg__(self) -> 'Fp':
        return Fp(self.P - self.v)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Fp):
            return False
        return self.v == other.v
    
    def __repr__(self) -> str:
        return f"Fp({hex(self.v)})"
    
    def __int__(self) -> int:
        return self.v
    
    def inv(self) -> 'Fp':
        """Modular inverse using Fermat's little theorem: a^(-1) = a^(p-2) mod p"""
        return Fp(pow(self.v, self.P - 2, self.P))
    
    def square(self) -> 'Fp':
        """Squaring operation."""
        return Fp(self.v * self.v)
    
    @classmethod
    def zero(cls) -> 'Fp':
        return cls(0)
    
    @classmethod
    def one(cls) -> 'Fp':
        return cls(1)


class Fp256:
    """
    Field element representation with explicit 256-bit width.
    
    This class is used for quantum circuit simulation where we need to track
    the bit-width of registers explicitly.
    """
    
    P = Fp.P
    BITS = 256
    
    def __init__(self, value: Union[int, Fp, 'Fp256']):
        if isinstance(value, Fp256):
            self.v = value.v
        elif isinstance(value, Fp):
            self.v = value.v
        else:
            self.v = value % self.P
    
    def to_bits(self) -> list[int]:
        """Convert to little-endian bit array (256 bits)."""
        bits = []
        val = self.v
        for _ in range(self.BITS):
            bits.append(val & 1)
            val >>= 1
        return bits
    
    @classmethod
    def from_bits(cls, bits: list[int]) -> 'Fp256':
        """Create from little-endian bit array."""
        value = 0
        for i, bit in enumerate(bits):
            if bit:
                value |= (1 << i)
        return cls(value)
    
    def __add__(self, other: 'Fp256') -> 'Fp256':
        return Fp256(self.v + other.v)
    
    def __sub__(self, other: 'Fp256') -> 'Fp256':
        return Fp256(self.v - other.v)
    
    def __mul__(self, other: 'Fp256') -> 'Fp256':
        return Fp256(self.v * other.v)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Fp256):
            return False
        return self.v == other.v
    
    def inv(self) -> 'Fp256':
        return Fp256(pow(self.v, self.P - 2, self.P))
    
    @classmethod
    def zero(cls) -> 'Fp256':
        return cls(0)
    
    @classmethod
    def one(cls) -> 'Fp256':
        return cls(1)
