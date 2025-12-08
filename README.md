# Confidential Multi-Agent Workflow

## Project Overview

This Proof of Concept (POC) implements a Secure State Transfer Protocol designed for distributed agentic systems. The objective is to demonstrate the secure exchange of sensitive intermediate state (Context) between two distinct agents executing within isolated Trusted Execution Environments (TEEs).

This architecture addresses the security risks inherent in standard orchestration frameworks where workflow state is typically persisted in plaintext. By integrating AWS Nitro Enclaves with Temporal, this solution ensures that the orchestration engine and the host infrastructure interact exclusively with encrypted data (ciphertext), while plaintext processing is confined strictly to the hardware-protected memory of the enclave.

## Core Objectives

1. **Confidentiality**: Verify that agent state remains encrypted at rest within the orchestration history and in transit through the host OS.
2. **Verifiability**: Implement cryptographic attestation to strictly bind decryption key access to specific, immutable software identities (PCR measurements).
3. **Durability**: Leverage Temporal for deterministic workflow execution without compromising data privacy.

## Architecture and Design

This POC implements a "Full Confidential Execution" model. The architecture divides the system into Untrusted (Host/Orchestrator) and Trusted (Enclave) domains.

### Component Breakdown

| Component | Technology | Role |
|-----------|------------|------|
| Trusted Compute | AWS Nitro Enclaves | Isolated execution environment for Agent logic, responsible for decryption, processing, and encryption. |
| Orchestrator | Temporal | Manages workflow state transitions and persists encrypted blobs (Ciphertext). |
| Key Management | AWS KMS | Stores the Trusted Session Key (TSK). Releases the key only upon validating the Enclave's attestation document. |
| Host Interface | vsock | Facilitates local socket communication between the untrusted Parent Instance and the Trusted Enclave. |
| Serialization | Protocol Buffers | Provides schema-bound binary serialization to ensure type safety and prevent deserialization attacks at the TEE boundary. |

### Data Flow: The Secure State Loop

The workflow executes a sequential transfer of state between Agent A and Agent B following this protocol:

1. **Bootstrapping (Agent A)**: The enclave initializes and requests the Trusted Session Key (TSK) from AWS KMS. KMS validates the enclave's PCR0 (software identity) before releasing the key.
2. **Encryption (Agent A)**: Agent A generates initial state, serializes it via Protobuf, and encrypts it using the TSK. The resulting ciphertext is returned to the host.
3. **Persistence (Host)**: The Temporal Worker receives the ciphertext via vsock and returns it to the Temporal Server. The server persists this blob in the Event History.
4. **Handoff (Agent B)**: Temporal triggers the next workflow step. The host passes the ciphertext from history to a new enclave instance (Agent B).
5. **Decryption (Agent B)**: Agent B performs independent attestation to retrieve the TSK, decrypts the input ciphertext, processes the data, and returns a new encrypted result.

## Prerequisites

- **Infrastructure**: AWS EC2 Instance (Parent) with Nitro Enclave support (e.g., m5.xlarge, c5.xlarge).
- **Operating System**: Amazon Linux 2 or 2023 with aws-nitro-enclaves-cli installed.
- **Orchestration Server**: Access to a Temporal Server (Temporal Cloud or Self-Hosted).
- **Language Runtime**: Python 3.9+ environment for both Host and Enclave logic.

## Getting Started

### Prerequisites

- **AWS CLI** configured with credentials (`aws configure`)
- **SQLite** (pre-installed on macOS, `apt install sqlite3` on Linux)
- Required AWS permissions: `AmazonEC2FullAccess`, `AWSKeyManagementServicePowerUser`, `IAMFullAccess`, `AmazonSSMFullAccess`

### Quick Start

```bash
# Clone the repository
git clone https://github.com/0xktn/confidential-multi-agent-workflow.git
cd confidential-multi-agent-workflow

# Set a passphrase for local state encryption
echo "your-passphrase" > INSECURE_PASSWORD_TEXT

# Run the automated setup (takes ~10 minutes)
./scripts/setup.sh
```

The setup script automatically:
1. Creates an EC2 instance with Nitro Enclave support
2. Configures KMS key with attestation policy  
3. Starts Temporal server on EC2
4. Builds and runs the enclave
5. Starts the host worker

### After Setup

```bash
# Check status
./scripts/setup.sh --remote-status

# SSH into the instance
ssh -i ~/.ssh/nitro-enclave-key.pem ec2-user@<instance-ip>

# Cleanup all resources
./scripts/setup.sh --clean
```

## Verification Procedure

To validate the success of the POC, confirm the following metrics:

1. **Confidentiality Verification**:
   - Access the Temporal Web UI.
   - Inspect the "Input" and "Result" payloads in the Event History.
   - Requirement: Data must appear as opaque binary/hex strings (ciphertext). No plaintext JSON should be visible.
2. **Attestation Verification**:
   - Query AWS CloudTrail logs for kms:Decrypt events.
   - Requirement: The event context must include a valid attestationDocument field, confirming the key was released only after hardware verification.
3. **Integrity Verification**:
   - Decrypt the final output of the workflow locally (using a debugging key or admin access).
   - Requirement: The final state must reflect modifications made by Agent B, proving the secure handoff and processing occurred successfully within the enclave boundary.

## Security Considerations

> [!CAUTION]
> This is a Proof of Concept implementation. Do not use in production without thorough security review and hardening.

### Key Security Features

- **Zero-Trust Architecture**: The orchestration layer never has access to plaintext data
- **Hardware-Backed Attestation**: Cryptographic proof of code identity before key release
- **Ephemeral Keys**: Session keys exist only in enclave memory and are never persisted
- **Immutable Execution**: PCR measurements ensure only approved code can decrypt data

### Known Limitations

- **Single Region**: This POC assumes all components operate within a single AWS region
- **Key Rotation**: Manual key rotation procedures are not implemented
- **Audit Logging**: Enhanced audit trails for compliance requirements need additional implementation
- **Network Isolation**: Additional network policies may be required for production deployments

## Troubleshooting

### Common Issues

**Issue**: `KMS Decrypt failed - Invalid attestation document`
- **Cause**: PCR0 mismatch between EIF and KMS policy
- **Solution**: Rebuild the enclave image and update the KMS key policy with the new PCR0 hash

**Issue**: `vsock connection refused`
- **Cause**: Enclave not running or incorrect CID/port
- **Solution**: Verify enclave is running with `nitro-cli describe-enclaves` and check vsock configuration

**Issue**: `Temporal workflow timeout`
- **Cause**: Enclave processing taking longer than workflow timeout
- **Solution**: Increase workflow timeout or optimize enclave processing logic

## Performance Considerations

- **Enclave Memory**: Allocate sufficient memory (minimum 512MB recommended) for cryptographic operations
- **vCPU Count**: At least 2 vCPUs recommended for production workloads
- **Network Latency**: vsock communication adds ~1-5ms overhead per call
- **Encryption Overhead**: AES-256-GCM encryption adds minimal overhead (<1ms for typical payloads)

## References

- **Orchestration Persistence**: [Temporal Persistence Documentation](https://docs.temporal.io/concepts/what-is-a-temporal-cluster#persistence)
- **Enclave Concepts**: [AWS Nitro Enclaves Concepts](https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave.html)
- **Key Management**: [Cryptographic Attestation in AWS KMS](https://docs.aws.amazon.com/kms/latest/developerguide/services-nitro-enclaves.html)
- **Temporal Documentation**: [Temporal.io](https://docs.temporal.io/)
- **Protocol Buffers**: [Protocol Buffers Documentation](https://protobuf.dev/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- AWS Nitro Enclaves team for providing robust TEE infrastructure
- Temporal.io for the durable workflow orchestration platform
- The confidential computing community for advancing privacy-preserving technologies

---

**Disclaimer**: This is a research prototype demonstrating confidential computing patterns. Always conduct thorough security audits before deploying similar architectures in production environments.