#!/usr/bin/env python3
"""
Test QPU-1 execution with correct Qreg syntax.
The error shows that Qreg uses method calls, not subscript notation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lapq.client import QPU1

# Test with correct Qreg syntax
test_circuits = [
    ("Bell State", """
q = Qreg(2)
q.H(0)
q.CNOT(0, 1)
print("Bell state result:")
print(q.measure())
"""),
    ("Simple X Gate", """
q = Qreg(4)
q.X(0)
q.X(2)
print("Qubits 0 and 2 set to |1>")
print(q.measure())
"""),
]

API_KEY = "demo-key-for-testing"
qpu = QPU1(API_KEY)

for name, code in test_circuits:
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")
    print(f"Code:\n{code}")
    print("-" * 70)
    
    try:
        result = qpu.run_fast(code, max_duration_seconds=60)
        print(f"Success: {result.success}")
        print(f"Status: {result.status}")
        print(f"Output:\n{result.output}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
