"""
Minimal Enclave Test - Phase 1

Just print and keep alive to verify Docker/Python works.
"""

import sys
import time
import traceback

try:
    print("=" * 60, flush=True)
    print("ENCLAVE STARTING...", flush=True)
    print(f"Python version: {sys.version}", flush=True)
    print(f"Working directory: {sys.path}", flush=True)
    print("=" * 60, flush=True)

    print("Testing imports...", flush=True)
    import socket
    print("✓ socket imported", flush=True)
    
    import json
    print("✓ json imported", flush=True)
    
    import logging
    print("✓ logging imported", flush=True)
    
    print("\nAll basic imports successful!", flush=True)
    print("Enclave is running. Keeping alive...", flush=True)
    print("=" * 60, flush=True)

    # Keep alive
    while True:
        time.sleep(60)
        print("Enclave heartbeat...", flush=True)
        
except Exception as e:
    print(f"\n{'='*60}", flush=True)
    print(f"FATAL ERROR: {e}", flush=True)
    print(f"{'='*60}", flush=True)
    traceback.print_exc()
    print(f"{'='*60}", flush=True)
    sys.exit(1)
