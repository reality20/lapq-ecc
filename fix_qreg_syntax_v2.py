#!/usr/bin/env python3
"""
Fix Qreg syntax from q[0].H() to q.H(0) format AND multi-qubit gates.
QPU-1 uses: q.H(0), q.CNOT(0, 1), q.CCNOT(0, 1, 2), q.CRz(0, 1, angle)
"""

import re

def fix_qreg_syntax(code):
    """Convert q[0].H() and q[a], q[b].GATE() style to q.GATE(a, b) style."""
    lines = code.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Pattern 1: q[index].GATE() -> q.GATE(index)
        match = re.match(r'^(\s*)q\[(\d+)\]\.(\w+)\((.*)\)$', line)
        if match:
            indent = match.group(1)
            qubit = match.group(2)
            gate = match.group(3)
            args = match.group(4)
            
            if args:
                new_line = f"{indent}q.{gate}({qubit}, {args})"
            else:
                new_line = f"{indent}q.{gate}({qubit})"
            fixed_lines.append(new_line)
            continue
        
        # Pattern 2: q[a], q[b].GATE() -> q.GATE(a, b)
        match = re.match(r'^(\s*)q\[(\d+)\],\s*q\[(\d+)\]\.(\w+)\((.*)\)$', line)
        if match:
            indent = match.group(1)
            qubit1 = match.group(2)
            qubit2 = match.group(3)
            gate = match.group(4)
            args = match.group(5)
            
            if args:
                new_line = f"{indent}q.{gate}({qubit1}, {qubit2}, {args})"
            else:
                new_line = f"{indent}q.{gate}({qubit1}, {qubit2})"
            fixed_lines.append(new_line)
            continue
        
        # Pattern 3: q[a], q[b], q[c].GATE() -> q.GATE(a, b, c)
        match = re.match(r'^(\s*)q\[(\d+)\],\s*q\[(\d+)\],\s*q\[(\d+)\]\.(\w+)\((.*)\)$', line)
        if match:
            indent = match.group(1)
            qubit1 = match.group(2)
            qubit2 = match.group(3)
            qubit3 = match.group(4)
            gate = match.group(5)
            args = match.group(6)
            
            if args:
                new_line = f"{indent}q.{gate}({qubit1}, {qubit2}, {qubit3}, {args})"
            else:
                new_line = f"{indent}q.{gate}({qubit1}, {qubit2}, {qubit3})"
            fixed_lines.append(new_line)
            continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

# Fix the adder file
with open('/workspace/qpu1_adder_4bit.qreg', 'r') as f:
    adder_code = f.read()

fixed_adder = fix_qreg_syntax(adder_code)
with open('/workspace/qpu1_adder_4bit_fixed.qreg', 'w') as f:
    f.write(fixed_adder)

print("Fixed adder code (first 40 lines):")
print("="*70)
for i, line in enumerate(fixed_adder.split('\n')[:40]):
    print(line)
print("...")
print("="*70)

# Fix the QFT file  
with open('/workspace/qpu1_qft_6qubit.qreg', 'r') as f:
    qft_code = f.read()

fixed_qft = fix_qreg_syntax(qft_code)
with open('/workspace/qpu1_qft_6qubit_fixed.qreg', 'w') as f:
    f.write(fixed_qft)

print("\nFixed QFT code (first 30 lines):")
print("="*70)
for i, line in enumerate(fixed_qft.split('\n')[:30]):
    print(line)
print("...")
print("="*70)
