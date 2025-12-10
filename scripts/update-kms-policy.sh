#!/bin/bash
# Update KMS Policy with PCR0
# FIX 2: Auto-sync PCR0 after enclave build

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/state.sh"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

PCR0="${1:-}"
if [[ -z "$PCR0" ]]; then
    PCR0=$(state_get "pcr0" 2>/dev/null || echo "")
fi

if [[ -z "$PCR0" ]]; then
    log_error "PCR0 not provided and not found in state"
    exit 1
fi

KMS_KEY_ID=$(state_get "kms_key_id" 2>/dev/null || echo "")
AWS_REGION=$(state_get "aws_region" 2>/dev/null || echo "ap-southeast-1")
AWS_ACCOUNT_ID=$(state_get "aws_account_id" 2>/dev/null || echo "")

if [[ -z "$KMS_KEY_ID" ]]; then
    log_error "KMS key ID not found in state"
    exit 1
fi

log_info "Updating KMS policy with PCR0: ${PCR0:0:32}..."

# Get current policy
CURRENT_POLICY=$(aws kms get-key-policy \
    --key-id "$KMS_KEY_ID" \
    --policy-name default \
    --region "$AWS_REGION" \
    --query "Policy" \
    --output text)

# Update PCR0 in policy using jq
NEW_POLICY=$(echo "$CURRENT_POLICY" | jq --arg pcr0 "$PCR0" '
    (.Statement[] | select(.Sid == "Allow Nitro Enclave Decrypt") | .Condition.StringEqualsIgnoreCase."kms:RecipientAttestation:PCR0") |= $pcr0
')

# Apply updated policy
echo "$NEW_POLICY" | aws kms put-key-policy \
    --key-id "$KMS_KEY_ID" \
    --policy-name default \
    --policy file:///dev/stdin \
    --region "$AWS_REGION"

log_info "KMS policy updated successfully!"
state_set "pcr0" "$PCR0" --encrypt
