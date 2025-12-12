# Tests

This directory contains test scripts for the confidential multi-agent workflow.

## Test Files

### Key Verification Scripts

- **`verify_attestation.py`**
  - **Purpose**: The primary verification tool. Checks both worker logs (immediate) and CloudTrail (audit) to confirm attestation success.
  - **Usage**: Called automatically by `./scripts/trigger.sh --verify`.

- **`test_kms_attestation.py`**
  - **Purpose**: A comprehensive end-to-end integration test.
  - **Flow**:
    1. Connects to enclave via vsock.
    2. Sends encrypted TSK (Trusted Session Key).
    3. Enclave requests attestation from AWS Nitro Hypervisor.
    4. Enclave sends attestation to AWS KMS to decrypt the TSK.
    5. Enclave uses TSK to decrypt payload.
  - **Usage**: Run manually to validate deep system integrity.

## Running Tests

### Standard Verification

```bash
# From project root
./scripts/trigger.sh --verify
```

### Deep System Test

```bash
# On the EC2 instance
python3 tests/test_kms_attestation.py
```

## Troubleshooting

**Test fails with "Connection refused"**
- Ensure enclave is running: `nitro-cli describe-enclaves`
- Ensure vsock-proxy is running: `ps aux | grep vsock-proxy`

**Test fails with "KMS Decrypt failed"**
- Verify PCR0 in KMS policy matches the running enclave build.
- Run verify command to see detailed logs.
