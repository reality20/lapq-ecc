#!/usr/bin/env python3
"""
Update QuantumCircuit.to_qreg() to generate correct QPU-1 syntax directly.
"""

import sys
sys.path.insert(0, '/workspace')

# Read the current core.py
with open('/workspace/ecdlp_solver/quantum/core.py', 'r') as f:
    core_code = f.read()

# Find and replace the to_qreg method
old_to_qreg = '''    def to_qreg(self, circuit_name: str = None, auto_measure: bool = False) -> str:
        \"\"\"Generate QPU-1 compatible Qreg code.\"\"\"
        lines = []
        name = circuit_name or self.name or "quantum_circuit"
        lines.append(f"# Quantum circuit: {name}")
        lines.append(f"q = Qreg({self.num_qubits})")
        lines.append("")
        
        for gate in self.gates:
            if gate[0] == 'X':
                lines.append(f"q[{gate[1][0]}].X()")
            elif gate[0] == 'H':
                lines.append(f"q[{gate[1][0]}].H()")
            elif gate[0] == 'CNOT':
                lines.append(f"q[{gate[1][0]}], q[{gate[1][1]}].CNOT()")
            elif gate[0] == 'CCNOT':
                lines.append(f"q[{gate[1][0]}], q[{gate[1][1]}], q[{gate[1][2]}].CCNOT()")
            elif gate[0] == 'CRz':
                angle = gate[1][2]
                lines.append(f"q[{gate[1][0]}], q[{gate[1][1]}].CRz({angle})")
            elif gate[0] == 'SWAP':
                lines.append(f"q[{gate[1][0]}], q[{gate[1][1]}].SWAP()")
        
        if auto_measure:
            lines.append("")
            lines.append(f"print(q.measure())")
        
        return "\\n".join(lines)'''

new_to_qreg = '''    def to_qreg(self, circuit_name: str = None, auto_measure: bool = False) -> str:
        \"\"\"Generate QPU-1 compatible Qreg code with correct syntax.\"\"\"
        lines = []
        name = circuit_name or self.name or "quantum_circuit"
        lines.append(f"# Quantum circuit: {name}")
        lines.append(f"q = Qreg({self.num_qubits})")
        lines.append("")
        
        for gate in self.gates:
            if gate[0] == 'X':
                lines.append(f"q.X({gate[1][0]})")
            elif gate[0] == 'H':
                lines.append(f"q.H({gate[1][0]})")
            elif gate[0] == 'CNOT':
                lines.append(f"q.CNOT({gate[1][0]}, {gate[1][1]})")
            elif gate[0] == 'CCNOT':
                lines.append(f"q.CCNOT({gate[1][0]}, {gate[1][1]}, {gate[1][2]})")
            elif gate[0] == 'CRz':
                angle = gate[1][2]
                lines.append(f"q.CRz({gate[1][0]}, {gate[1][1]}, {angle})")
            elif gate[0] == 'SWAP':
                lines.append(f"q.SWAP({gate[1][0]}, {gate[1][1]})")
        
        if auto_measure:
            lines.append("")
            lines.append(f"print(q.measure())")
        
        return "\\n".join(lines)'''

if old_to_qreg in core_code:
    core_code = core_code.replace(old_to_qreg, new_to_qreg)
    with open('/workspace/ecdlp_solver/quantum/core.py', 'w') as f:
        f.write(core_code)
    print("✓ Updated to_qreg() method in core.py")
else:
    print("⚠ Could not find exact to_qreg() method to replace")
    print("Searching for alternative patterns...")
    
# Verify the change
with open('/workspace/ecdlp_solver/quantum/core.py', 'r') as f:
    updated_code = f.read()

if 'q.X({gate[1][0]})' in updated_code:
    print("✓ Confirmed: QPU-1 syntax update successful!")
else:
    print("⚠ Update may not have been applied correctly")
