#!/usr/bin/env python3
"""
Execute quantum circuits on QPU-1 using the Gradio API endpoint.
Uses the client.py implementation to submit jobs and retrieve results.
"""

import sys
import os
sys.path.insert(0, '/workspace')

from client import QPU1

# Get API key from environment or use demo key
API_KEY = os.environ.get('QPU1_API_KEY', 'demo-key-for-testing')

def execute_qreg_file(qreg_file_path: str, description: str = ""):
    """Load a .qreg file and execute it on QPU-1."""
    print(f"\n{'='*70}")
    print(f"Executing on QPU-1: {os.path.basename(qreg_file_path)}")
    if description:
        print(f"Description: {description}")
    print(f"{'='*70}\n")
    
    # Read the Qreg code
    with open(qreg_file_path, 'r') as f:
        qreg_code = f.read()
    
    if not qreg_code.strip():
        print(f"ERROR: {qreg_file_path} is empty!")
        return None
    
    print("Qreg code preview (first 20 lines):")
    print("-" * 70)
    for i, line in enumerate(qreg_code.split('\n')[:20]):
        print(line)
    if len(qreg_code.split('\n')) > 20:
        print(f"... ({len(qreg_code.split(chr(10))) - 20} more lines)")
    print("-" * 70)
    
    # Initialize QPU-1 client
    try:
        qpu = QPU1(API_KEY)
    except ValueError as e:
        print(f"ERROR initializing QPU-1 client: {e}")
        print(f"Get your API key at: https://qpu-1.lovable.app/api-access")
        return None
    
    # Execute on QPU-1 using the fast Gradio channel
    print("\nSubmitting to QPU-1 (Gradio fast channel)...")
    print("This may take a moment depending on queue...")
    
    try:
        result = qpu.run_fast(qreg_code, max_duration_seconds=300)
        
        print("\n" + "="*70)
        print("EXECUTION RESULT")
        print("="*70)
        print(f"Success: {result.success}")
        print(f"Job ID: {result.job_id}")
        print(f"Status: {result.status}")
        print(f"\nOutput:\n{result.output}")
        print("="*70)
        
        return result
        
    except Exception as e:
        print(f"\nERROR during execution: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Execute all available .qreg files on QPU-1."""
    qreg_files = [
        ("/workspace/qpu1_adder_4bit.qreg", "4-bit Cuccaro adder: 5 + 3 = 8"),
        ("/workspace/qpu1_qft_6qubit.qreg", "6-qubit Quantum Fourier Transform"),
    ]
    
    results = []
    for qreg_file, description in qreg_files:
        if os.path.exists(qreg_file):
            result = execute_qreg_file(qreg_file, description)
            results.append((qreg_file, result))
        else:
            print(f"\nWARNING: {qreg_file} not found, skipping...")
    
    # Summary
    print("\n" + "="*70)
    print("EXECUTION SUMMARY")
    print("="*70)
    for qreg_file, result in results:
        status = "✓ SUCCESS" if result and result.success else "✗ FAILED"
        print(f"{status}: {os.path.basename(qreg_file)}")
        if result and result.output:
            # Extract first line of output
            first_line = result.output.split('\n')[0][:60]
            print(f"         Output: {first_line}...")
    print("="*70)

if __name__ == "__main__":
    main()
