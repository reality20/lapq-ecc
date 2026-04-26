# Fix Qreg format to match QPU-1 syntax
with open('/workspace/ecdlp_full_circuit.qreg', 'r') as f:
    content = f.read()

# Fix gate format: q.GATE([q0, q1], []) -> q[q0], q[q1].GATE()
import re

def fix_gate(match):
    gate_name = match.group(1)
    qubits_str = match.group(2)
    
    # Parse qubits list
    qubits = eval(qubits_str)
    
    if len(qubits) == 1:
        return f"q[{qubits[0]}].{gate_name}()"
    elif len(qubits) == 2:
        return f"q[{qubits[0]}], q[{qubits[1]}].{gate_name}()"
    elif len(qubits) == 3:
        return f"q[{qubits[0]}], q[{qubits[1]}], q[{qubits[2]}].{gate_name}()"
    else:
        # Multi-qubit gate
        controls = ", ".join([f"q[{q}]" for q in qubits[:-1]])
        target = f"q[{qubits[-1]}]"
        return f"{controls}, {target}.{gate_name}()"

# Fix single-qubit gates
content = re.sub(r'q\.(H|X|Y|Z|S|T)\(\[(\d+)\], \[\]\)', r'q[\2].\1()', content)

# Fix two-qubit gates  
content = re.sub(r'q\.(CNOT|CRz|SWAP)\(\[(\d+), (\d+)\], \[\]\)', r'q[\2], q[\3].\1()', content)

# Fix three-qubit gates
content = re.sub(r'q\.(CCNOT|CSWAP)\(\[(\d+), (\d+), (\d+)\], \[\]\)', r'q[\2], q[\3], q[\4].\1()', content)

# Fix measurement
content = content.replace('print(q.measure())', '# Measure all output qubits\n# print(q.measure())')

with open('/workspace/ecdlp_secp256k1_fixed.qreg', 'w') as f:
    f.write(content)
    
print("Fixed Qreg file saved to /workspace/ecdlp_secp256k1_fixed.qreg")
print(f"Size: {len(content)} bytes")
