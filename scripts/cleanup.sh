#!/bin/bash
# Cleanup Script
# Removes all resources created by setup scripts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/state.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo -e "${RED}WARNING: This will delete all POC resources!${NC}"
echo ""
state_status
echo ""
read -p "Are you sure? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Get values from state
AWS_REGION=$(state_get "aws_region" 2>/dev/null || echo "")
INSTANCE_ID=$(state_get "instance_id" 2>/dev/null || echo "")
SG_ID=$(state_get "sg_id" 2>/dev/null || echo "")
KEY_NAME=$(state_get "key_name" 2>/dev/null || echo "")
KEY_ID=$(state_get "kms_key_id" 2>/dev/null || echo "")
KEY_ALIAS=$(state_get "kms_key_alias" 2>/dev/null || echo "")
ROLE_NAME=$(state_get "iam_role_name" 2>/dev/null || echo "")
TEMPORAL_DIR=$(state_get "temporal_dir" 2>/dev/null || echo "")

# Terminate EC2
if [ -n "$INSTANCE_ID" ] && [ -n "$AWS_REGION" ]; then
    log_info "Terminating EC2: $INSTANCE_ID"
    aws ec2 terminate-instances --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" 2>/dev/null || true
    aws ec2 wait instance-terminated --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" 2>/dev/null || true
fi

# Delete security group
if [ -n "$SG_ID" ] && [ -n "$AWS_REGION" ]; then
    log_info "Deleting security group: $SG_ID"
    aws ec2 delete-security-group --region "$AWS_REGION" --group-id "$SG_ID" 2>/dev/null || true
fi

# Delete key pair
if [ -n "$KEY_NAME" ] && [ -n "$AWS_REGION" ]; then
    log_info "Deleting key pair: $KEY_NAME"
    aws ec2 delete-key-pair --region "$AWS_REGION" --key-name "$KEY_NAME" 2>/dev/null || true
    rm -f ~/.ssh/${KEY_NAME}.pem
fi

# Delete KMS
if [ -n "$KEY_ALIAS" ] && [ -n "$AWS_REGION" ]; then
    log_info "Deleting KMS alias..."
    aws kms delete-alias --region "$AWS_REGION" --alias-name "alias/${KEY_ALIAS}" 2>/dev/null || true
fi

if [ -n "$KEY_ID" ] && [ -n "$AWS_REGION" ]; then
    log_info "Scheduling KMS key deletion..."
    aws kms schedule-key-deletion --region "$AWS_REGION" --key-id "$KEY_ID" --pending-window-in-days 7 2>/dev/null || true
fi

# Delete IAM
if [ -n "$ROLE_NAME" ]; then
    log_info "Deleting IAM resources..."
    aws iam remove-role-from-instance-profile --instance-profile-name EnclaveInstanceProfile --role-name "$ROLE_NAME" 2>/dev/null || true
    aws iam delete-instance-profile --instance-profile-name EnclaveInstanceProfile 2>/dev/null || true
    aws iam delete-role-policy --role-name "$ROLE_NAME" --policy-name KMSDecryptPolicy 2>/dev/null || true
    aws iam delete-role --role-name "$ROLE_NAME" 2>/dev/null || true
fi

# Stop Temporal
if [ -n "$TEMPORAL_DIR" ] && [ -d "$TEMPORAL_DIR" ]; then
    log_info "Stopping Temporal..."
    cd "$TEMPORAL_DIR"
    docker compose down -v 2>/dev/null || true
    cd ..
    rm -rf "$TEMPORAL_DIR"
fi

# Clean local files
rm -f encrypted-tsk.b64 encrypted-tsk.bin
rm -rf ./config ./build

# Reset state
state_reset

log_info "Cleanup complete!"
