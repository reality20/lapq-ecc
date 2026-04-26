#!/usr/bin/env python3
"""
Execute the fixed Qreg circuits on QPU-1.
"""

import sys
sys.path.insert(0, '/workspace')

from client import QPU1

API_KEY = "demo-key-for-testing"
qpu = QPU1(API_KEY)

# Test the fixed adder
with open('/workspace/qpu1_adder_4bit_fixed.qreg', 'r') as f:
    adder_code = f.read()

print("="*70)
print("Executing 4-bit Cuccaro Adder on QPU-1")
print("Computing: 5 + 3 = 8")
print("="*70)
print("\nQreg code (first 25 lines):")
for line in adder_code.split('\n')[:25]:
    print(line)
print("...")
print("="*70)

result = qpu.run_fast(adder_code, max_duration_seconds=60)
print(f"\nResult:")
print(f"Success: {result.success}")
print(f"Status: {result.status}")
print(f"Output:\n{result.output}")
print("="*70)

# Test the fixed QFT
with open('/workspace/qpu1_qft_6qubit_fixed.qreg', 'r') as f:
    qft_code = f.read()

print("\n" + "="*70)
print("Executing 6-qubit QFT on QPU-1")
print("="*70)
print("\nQreg code (first 20 lines):")
for line in qft_code.split('\n')[:20]:
    print(line)
print("...")
print("="*70)

result = qpu.run_fast(qft_code, max_duration_seconds=60)
print(f"\nResult:")
print(f"Success: {result.success}")
print(f"Status: {result.status}")
print(f"Output:\n{result.output}")
print("="*70)
