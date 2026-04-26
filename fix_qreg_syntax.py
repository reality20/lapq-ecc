#!/usr/bin/env python3
"""
Fix Qreg syntax from q[0].H() to q.H(0) format for QPU-1 compatibility.
"""

import re

def fix_qreg_syntax(code):
    """Convert q[0].H() style to q.H(0) style."""
    lines = code.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Pattern: q[index].GATE() -> q.GATE(index)
        # Match q[digit].GATE(args) or q[digit].GATE()
        match = re.match(r'^(\s*)q\[(\d+)\]\.(\w+)\((.*)\)$', line)
        if match:
            indent = match.group(1)
            qubit = match.group(2)
            gate = match.group(3)
            args = match.group(4)
            
            if args:
                # Gate has arguments like CRz(angle)
                new_line = f"{indent}q.{gate}({qubit}, {args})"
            else:
                # Gate has no arguments like H()
                new_line = f"{indent}q.{gate}({qubit})"
            fixed_lines.append(new_line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

# Fix the adder file
with open('/workspace/qpu1_adder_4bit.qreg', 'r') as f:
    adder_code = f.read()

fixed_adder = fix_qreg_syntax(adder_code)
with open('/workspace/qpu1_adder_4bit_fixed.qreg', 'w') as f:
    f.write(fixed_adder)

print("Fixed adder code:")
print("="*70)
print(fixed_adder[:500])
print("...")
print("="*70)

# Fix the QFT file
with open('/workspace/qpu1_qft_6qubit.qreg', 'r') as f:
    qft_code = f.read()

fixed_qft = fix_qreg_syntax(qft_code)
with open('/workspace/qpu1_qft_6qubit_fixed.qreg', 'w') as f:
    f.write(fixed_qft)

print("\nFixed QFT code:")
print("="*70)
print(fixed_qft[:500])
print("...")
