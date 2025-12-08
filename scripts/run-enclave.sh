#!/bin/bash
# Run Enclave
# See docs/04-enclave-development.md for details

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EIF_PATH="$PROJECT_ROOT/build/enclave.eif"

# Default configuration
CPU_COUNT="${CPU_COUNT:-2}"
MEMORY_MB="${MEMORY_MB:-1024}"
DEBUG_MODE="${DEBUG_MODE:-false}"

if [ ! -f "$EIF_PATH" ]; then
  echo "Error: Enclave image not found at $EIF_PATH"
  echo "Run scripts/build-enclave.sh first."
  exit 1
fi

echo "Starting enclave..."
echo "  CPU Count: $CPU_COUNT"
echo "  Memory: ${MEMORY_MB}MB"
echo "  Debug Mode: $DEBUG_MODE"

if [ "$DEBUG_MODE" = "true" ]; then
  nitro-cli run-enclave \
    --cpu-count "$CPU_COUNT" \
    --memory "$MEMORY_MB" \
    --eif-path "$EIF_PATH" \
    --debug-mode
else
  nitro-cli run-enclave \
    --cpu-count "$CPU_COUNT" \
    --memory "$MEMORY_MB" \
    --eif-path "$EIF_PATH"
fi

echo ""
echo "Enclave started. Use 'nitro-cli describe-enclaves' to see status."
echo "Note the EnclaveCID for host worker configuration."
