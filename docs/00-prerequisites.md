# Prerequisites

Install required tools and configure AWS access before running setup.

## 1. Install Tools

### AWS CLI

```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Verify
aws --version
```

### SQLite

```bash
# macOS (pre-installed)
sqlite3 --version

# Linux
sudo apt install sqlite3
```

## 2. Configure AWS

```bash
aws configure
# AWS Access Key ID: (from IAM console)
# AWS Secret Access Key: (from IAM console)
# Default region: ap-southeast-1
# Default output: json
```

Verify:
```bash
aws sts get-caller-identity
```

> [!NOTE]
> Your IAM user needs: `AmazonEC2FullAccess`, `AWSKeyManagementServicePowerUser`, `IAMFullAccess`, `AmazonSSMFullAccess`

## 3. Setup Passphrase

```bash
echo "your-passphrase" > INSECURE_PASSWORD_TEXT
```

> [!WARNING]
> This file stores the passphrase for encrypting local state. Add to `.gitignore`.

## 4. Run Setup

```bash
./scripts/setup.sh
```

The script runs 8 automated steps:
1. EC2 instance with Nitro Enclave support
2. KMS key with attestation-based policy
3. Instance setup (Docker, Nitro CLI)
4. Temporal server on EC2
5. Enclave build (PCR0 extraction)
6. KMS policy with PCR0 attestation
7. Enclave start
8. Host worker start

Progress is saved, so you can resume if interrupted.

## Commands

```bash
# Check local state
./scripts/setup.sh --status

# Check remote (EC2) status
./scripts/setup.sh --remote-status

# Reset local state only
./scripts/setup.sh --reset

# Cleanup all AWS resources
./scripts/setup.sh --clean
```

## Next Steps

After setup completes, see [Verification Procedure](../README.md#verification-procedure) to validate the POC.
