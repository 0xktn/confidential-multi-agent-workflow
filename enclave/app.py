"""
Minimal Enclave Test - Phase 1

Just print and keep alive to verify Docker/Python works.
"""

import sys
import time

print("=" * 60, flush=True)
print("ENCLAVE STARTING...", flush=True)
print(f"Python version: {sys.version}", flush=True)
print("=" * 60, flush=True)

try:
    print("Testing imports...", flush=True)
    import socket
    print("✓ socket imported", flush=True)
    
    import json
    print("✓ json imported", flush=True)
    
    import logging
    print("✓ logging imported", flush=True)
    
    print("\nAll basic imports successful!", flush=True)
    
except Exception as e:
    print(f"✗ Import failed: {e}", flush=True)
    sys.exit(1)

print("\nEnclave is running. Keeping alive...", flush=True)
print("=" * 60, flush=True)

# Keep alive
while True:
    time.sleep(60)
    print("Enclave heartbeat...", flush=True)
