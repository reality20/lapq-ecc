#!/usr/bin/env python3
"""
ECDLP Measurement Result Parser & Private Key Recovery

secp256k1 generator point P is hardcoded.

This script lets you paste raw QPU-1 measurement results (bit-strings,
hex values, or JSON output) and automatically parses them to recover
the private key  k  such that  Q = kP.

Usage:
    python parse_measurement.py                  # interactive mode
    python parse_measurement.py --c 0x... --d 0x...   # direct values
    python parse_measurement.py --file result.txt     # from file
    echo '{"c": "0x...", "d": "0x..."}' | python parse_measurement.py --stdin
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ecdlp_solver.classical.field import Fp
from ecdlp_solver.classical.curve import ECPoint, secp256k1_generator, secp256k1_order
from ecdlp_solver.classical.postprocess import recover_private_key, extended_gcd


# ═══════════════════════════════════════════════════════════════════════════
# secp256k1 generator point P (hardcoded)
# ═══════════════════════════════════════════════════════════════════════════

P = secp256k1_generator()
N = secp256k1_order()  # group order

# Verify P is on curve at startup
_lhs = Fp(int(P.y)) * Fp(int(P.y))
_rhs = Fp(int(P.x)) ** 3 + Fp(7)
assert _lhs == _rhs, "Generator point P is not on the secp256k1 curve!"

print(f"secp256k1 Generator P:")
print(f"  P.x = {hex(int(P.x))}")
print(f"  P.y = {hex(int(P.y))}")
print(f"  Order n = {hex(N)}")
print()


# ═══════════════════════════════════════════════════════════════════════════
# Parsing helpers
# ═══════════════════════════════════════════════════════════════════════════

def parse_int(s: str) -> int:
    """Parse a string as an integer (supports hex 0x..., binary 0b..., decimal)."""
    s = s.strip().lower().replace(" ", "").replace("_", "")
    if s.startswith("0x"):
        return int(s, 16)
    elif s.startswith("0b"):
        return int(s, 2)
    else:
        return int(s)


def bitstring_to_int(bits: str, endian: str = "big") -> int:
    """Convert a string of '0' and '1' characters to an integer.
    
    Args:
        bits: String of '0' and '1' characters.
        endian: 'big' (MSB first, default) or 'little' (LSB first).
    """
    bits = bits.strip()
    if not all(c in "01" for c in bits):
        raise ValueError(f"Not a valid bit-string: {bits!r}")
    if endian == "little":
        bits = bits[::-1]
    return int(bits, 2)


def parse_bitstring_pair(raw: str, n_bits: int = 256, endian: str = "big") -> tuple[int, int]:
    """
    Parse a single measurement bit-string into (c, d).
    
    The bit-string is expected to be 2*n_bits long, where the first
    n_bits are register 'a' (yielding c) and the last n_bits are
    register 'b' (yielding d).
    """
    raw = raw.strip().replace(" ", "").replace("\n", "")
    if not all(c in "01" for c in raw):
        raise ValueError(f"Not a valid bit-string: {raw[:50]!r}...")
    
    if len(raw) != 2 * n_bits:
        print(f"  Warning: Expected {2 * n_bits} bits, got {len(raw)} bits.")
        print(f"  Splitting at midpoint ({len(raw) // 2} bits each).")
        n_bits = len(raw) // 2
    
    a_bits = raw[:n_bits]
    b_bits = raw[n_bits:2 * n_bits]
    
    c = bitstring_to_int(a_bits, endian)
    d = bitstring_to_int(b_bits, endian)
    return c, d


def parse_raw_output(text: str) -> list[tuple[int, int]]:
    """
    Auto-detect and parse measurement results from raw QPU-1 output.
    
    Supported formats:
    - Single bit-string (512 binary digits)
    - JSON with "c" and "d" fields (hex or decimal)
    - JSON with "measurements" array
    - Newline-separated c,d pairs (hex or decimal)
    - QPU-1 output format: "Result: 01001..." or "bits: 01001..."
    - Multiple measurement lines
    
    Returns a list of (c, d) tuples.
    """
    text = text.strip()
    results: list[tuple[int, int]] = []
    
    # Try JSON first
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            if "c" in data and "d" in data:
                return [(parse_int(str(data["c"])), parse_int(str(data["d"])))]
            if "measurements" in data:
                for m in data["measurements"]:
                    if isinstance(m, dict) and "c" in m and "d" in m:
                        results.append((parse_int(str(m["c"])), parse_int(str(m["d"]))))
                    elif isinstance(m, str):
                        results.append(parse_bitstring_pair(m))
                return results
            if "bits" in data:
                return [parse_bitstring_pair(str(data["bits"]))]
            if "output" in data:
                return parse_raw_output(str(data["output"]))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "c" in item and "d" in item:
                    results.append((parse_int(str(item["c"])), parse_int(str(item["d"]))))
                elif isinstance(item, str):
                    results.append(parse_bitstring_pair(item))
            return results
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Try key=value lines:  c = 0x..., d = 0x...
    c_match = re.search(r'(?:^|\s)c\s*[=:]\s*([0-9a-fA-Fx]+)', text, re.MULTILINE)
    d_match = re.search(r'(?:^|\s)d\s*[=:]\s*([0-9a-fA-Fx]+)', text, re.MULTILINE)
    if c_match and d_match:
        return [(parse_int(c_match.group(1)), parse_int(d_match.group(1)))]
    
    # Try "c,d" or "c d" or "c\td" pairs per line (hex or decimal)
    lines = text.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        
        # Strip common prefixes
        for prefix in ["Result:", "result:", "bits:", "Bits:", "output:", "Output:"]:
            if line.startswith(prefix):
                line = line[len(prefix):].strip()
        
        # Pure bit-string
        cleaned = line.replace(" ", "")
        if all(c in "01" for c in cleaned) and len(cleaned) >= 4:
            results.append(parse_bitstring_pair(cleaned))
            continue
        
        # Comma/space/tab separated pair of numbers
        parts = re.split(r'[,\s\t]+', line)
        if len(parts) == 2:
            try:
                c_val = parse_int(parts[0])
                d_val = parse_int(parts[1])
                results.append((c_val, d_val))
                continue
            except ValueError:
                pass
        
        # Single hex number — treat as bit-string equivalent
        try:
            val = parse_int(line)
            # If it's very large (512+ bits), split in half
            bit_len = val.bit_length()
            if bit_len > 256:
                half = bit_len // 2
                c_val = val >> half
                d_val = val & ((1 << half) - 1)
                results.append((c_val, d_val))
            continue
        except ValueError:
            pass
    
    return results


# ═══════════════════════════════════════════════════════════════════════════
# Key recovery
# ═══════════════════════════════════════════════════════════════════════════

def try_recover_key(
    c: int,
    d: int,
    Q: ECPoint | None = None,
    verbose: bool = True,
) -> int | None:
    """
    Attempt to recover the private key k from a single (c, d) measurement.
    
    The relation is:  c·k + d ≡ 0 (mod n)
    So:               k = -d · c⁻¹ mod n
    
    Args:
        c: Measurement from register a.
        d: Measurement from register b.
        Q: The target public key Q = kP (for verification). None to skip.
        verbose: Print details.
    
    Returns:
        The private key k if c ≠ 0, else None.
    """
    if verbose:
        print(f"  c = {hex(c)}")
        print(f"  d = {hex(d)}")
        print(f"  c (dec) = {c}")
        print(f"  d (dec) = {d}")
    
    if c == 0:
        if verbose:
            print("  ✗ c = 0 — cannot recover k (need to re-run quantum circuit)")
        return None
    
    if c >= N:
        if verbose:
            print(f"  ⚠ c >= n, reducing mod n")
        c = c % N
    if d >= N:
        if verbose:
            print(f"  ⚠ d >= n, reducing mod n")
        d = d % N
    
    # k = -d * c^(-1) mod n
    k = recover_private_key(c, d, n=N, P=P, Q=Q, verify=(Q is not None))
    
    if k is not None:
        if verbose:
            print(f"  ✓ Recovered k = {hex(k)}")
            print(f"    k (dec) = {k}")
            print(f"    k (bits) = {k.bit_length()} bits")
            if Q is not None:
                print(f"  ✓ Verified: kP = Q")
    else:
        if verbose:
            print(f"  ⚠ Key computation gave k = -d·c⁻¹ mod n = {hex((-d * pow(c, N-2, N)) % N)}")
            print(f"    but kP ≠ Q — this measurement may be noisy")
    
    return k


def recover_from_multiple(
    measurements: list[tuple[int, int]],
    Q: ECPoint | None = None,
    verbose: bool = True,
) -> int | None:
    """
    Try to recover the private key from multiple (c, d) measurements.
    
    If a single valid measurement suffices, returns immediately.
    Multiple measurements can be combined using lattice/CRT techniques.
    """
    print(f"\n{'='*70}")
    print(f"  Processing {len(measurements)} measurement(s)")
    print(f"{'='*70}")
    
    valid_keys: list[int] = []
    
    for i, (c, d) in enumerate(measurements):
        print(f"\n--- Measurement {i+1}/{len(measurements)} ---")
        k = try_recover_key(c, d, Q=Q, verbose=verbose)
        if k is not None and k != 0:
            valid_keys.append(k)
    
    if not valid_keys:
        print(f"\n✗ No valid key recovered from {len(measurements)} measurement(s).")
        print("  Possible causes:")
        print("    - c = 0 in all measurements (re-run quantum circuit)")
        print("    - Measurement noise / decoherence")
        print("    - Wrong Q (public key) provided for verification")
        return None
    
    # Check if all recovered keys agree
    if len(set(valid_keys)) == 1:
        k = valid_keys[0]
        print(f"\n{'='*70}")
        print(f"  ✓ PRIVATE KEY RECOVERED")
        print(f"    k = {hex(k)}")
        print(f"    k (dec) = {k}")
        print(f"    from {len(valid_keys)}/{len(measurements)} valid measurement(s)")
        print(f"{'='*70}")
        return k
    else:
        # Multiple different candidates — pick most common
        from collections import Counter
        counter = Counter(valid_keys)
        best_k, count = counter.most_common(1)[0]
        print(f"\n  ⚠ Multiple key candidates found:")
        for k_val, cnt in counter.most_common():
            print(f"    k = {hex(k_val)}  (appeared {cnt} time(s))")
        print(f"\n  Best candidate (majority): k = {hex(best_k)}")
        return best_k


# ═══════════════════════════════════════════════════════════════════════════
# Interactive mode
# ═══════════════════════════════════════════════════════════════════════════

def interactive_mode():
    """Run the interactive measurement parser."""
    print("="*70)
    print("  ECDLP Measurement Parser — Interactive Mode")
    print("  Paste your QPU-1 measurement result below.")
    print("  Supported formats:")
    print("    • Bit-string (512 binary digits, MSB first)")
    print("    • c,d pair (hex or decimal, comma or space separated)")
    print("    • JSON: {\"c\": \"0x...\", \"d\": \"0x...\"}")
    print("    • JSON: {\"measurements\": [{\"c\": ..., \"d\": ...}, ...]}")
    print("    • Key-value: c = 0x...  d = 0x...")
    print("  Type 'quit' or Ctrl+D to exit.")
    print("="*70)
    
    # Optionally provide Q for verification
    Q = None
    q_input = input("\nPublic key Q (hex x-coordinate, or 'skip'): ").strip()
    if q_input and q_input.lower() != "skip":
        try:
            qx = parse_int(q_input)
            # Recover y from x using curve equation y² = x³ + 7
            x_fp = Fp(qx)
            y2 = x_fp ** 3 + Fp(7)
            # Compute sqrt using Tonelli-Shanks (for p ≡ 3 mod 4, y = y2^((p+1)/4))
            y_fp = y2 ** ((Fp.P + 1) // 4)
            if (y_fp * y_fp) == y2:
                # Default to even y
                y_val = int(y_fp)
                if y_val % 2 == 1:
                    y_val = Fp.P - y_val
                Q = ECPoint(qx, y_val)
                print(f"  Q = ({hex(qx)}, {hex(y_val)})")
                
                # Ask about y parity
                parity = input("  Y parity (even/odd, default=even): ").strip().lower()
                if parity == "odd":
                    Q = ECPoint(qx, Fp.P - y_val)
                    print(f"  Q updated with odd y")
            else:
                print(f"  ⚠ x={hex(qx)} is not on the curve, skipping verification")
        except Exception as e:
            print(f"  ⚠ Could not parse Q: {e}, skipping verification")
    
    print("\nPaste your measurement result (press Enter twice when done):")
    print("-" * 70)
    
    while True:
        lines = []
        empty_count = 0
        try:
            while True:
                line = input()
                if line.strip().lower() in ("quit", "exit", "q"):
                    print("Goodbye!")
                    return
                if line.strip() == "":
                    empty_count += 1
                    if empty_count >= 2:
                        break
                    lines.append(line)
                else:
                    empty_count = 0
                    lines.append(line)
        except EOFError:
            if not lines:
                print("\nGoodbye!")
                return
        
        raw = "\n".join(lines).strip()
        if not raw:
            continue
        
        try:
            measurements = parse_raw_output(raw)
            if not measurements:
                print("  ⚠ Could not parse any (c, d) pairs from input.")
                print("  Please check the format and try again.")
            else:
                recover_from_multiple(measurements, Q=Q)
        except Exception as e:
            print(f"  ✗ Parse error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "-"*70)
        print("Paste another measurement (or 'quit' to exit):")
        print("-" * 70)


# ═══════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Parse ECDLP measurement results and recover private keys.",
        epilog="P is the secp256k1 generator point (hardcoded).",
    )
    parser.add_argument("--c", type=str, default=None,
                        help="Measurement c value (hex or decimal)")
    parser.add_argument("--d", type=str, default=None,
                        help="Measurement d value (hex or decimal)")
    parser.add_argument("--file", type=str, default=None,
                        help="Read measurement results from a file")
    parser.add_argument("--stdin", action="store_true",
                        help="Read measurement results from stdin (pipe mode)")
    parser.add_argument("--qx", type=str, default=None,
                        help="Public key Q x-coordinate (hex) for verification")
    parser.add_argument("--qy", type=str, default=None,
                        help="Public key Q y-coordinate (hex) for verification")
    parser.add_argument("--bits", type=int, default=256,
                        help="Bit width per register (default: 256)")
    parser.add_argument("--endian", choices=["big", "little"], default="big",
                        help="Bit-string endianness (default: big = MSB first)")
    
    args = parser.parse_args()
    
    # Build Q if provided
    Q = None
    if args.qx:
        qx = parse_int(args.qx)
        if args.qy:
            qy = parse_int(args.qy)
        else:
            # Recover y from curve equation
            x_fp = Fp(qx)
            y2 = x_fp ** 3 + Fp(7)
            y_fp = y2 ** ((Fp.P + 1) // 4)
            if (y_fp * y_fp) == y2:
                qy = int(y_fp)
                if qy % 2 == 1:
                    qy = Fp.P - qy
            else:
                print(f"⚠ x={hex(qx)} is not a valid curve point, skipping verification")
                qx = None
        if qx is not None:
            Q = ECPoint(qx, qy)
            print(f"Public key Q: ({hex(qx)}, {hex(qy)})")
    
    # Direct c,d input
    if args.c is not None and args.d is not None:
        c = parse_int(args.c)
        d = parse_int(args.d)
        recover_from_multiple([(c, d)], Q=Q)
        return
    
    # File input
    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
        measurements = parse_raw_output(text)
        if measurements:
            recover_from_multiple(measurements, Q=Q)
        else:
            print("✗ Could not parse any measurements from file.")
        return
    
    # Stdin pipe mode
    if args.stdin:
        text = sys.stdin.read()
        measurements = parse_raw_output(text)
        if measurements:
            recover_from_multiple(measurements, Q=Q)
        else:
            print("✗ Could not parse any measurements from stdin.")
        return
    
    # Default: interactive mode
    interactive_mode()


if __name__ == "__main__":
    main()
