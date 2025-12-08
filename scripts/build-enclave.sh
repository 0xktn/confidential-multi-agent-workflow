#!/bin/bash
# Build Enclave Image (EIF)
# See docs/04-enclave-development.md for details

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENCLAVE_DIR="$PROJECT_ROOT/enclave"
OUTPUT_DIR="$PROJECT_ROOT/build"

echo "Building enclave Docker image..."
docker build -t confidential-enclave:latest "$ENCLAVE_DIR"

echo "Creating output directory..."
mkdir -p "$OUTPUT_DIR"

echo "Building Enclave Image File (EIF)..."
nitro-cli build-enclave \
  --docker-uri confidential-enclave:latest \
  --output-file "$OUTPUT_DIR/enclave.eif"

echo ""
echo "=========================================="
echo "IMPORTANT: Save the PCR0 value above!"
echo "Update your KMS key policy with this value."
echo "See docs/02-kms-configuration.md for details."
echo "=========================================="
