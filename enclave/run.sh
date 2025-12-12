#!/bin/sh
# Minimal test - just echo and sleep to verify enclave can run
echo "[ENCLAVE] ==============================" > /dev/console
echo "[ENCLAVE] Minimal test starting..." > /dev/console
echo "[ENCLAVE] If you see this, enclave is working!" > /dev/console
echo "[ENCLAVE] ==============================" > /dev/console

# Keep enclave alive
echo "[ENCLAVE] Sleeping forever..." > /dev/console
sleep infinity
