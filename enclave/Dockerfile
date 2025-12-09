# Use our pre-built kmstool-enclave image from GHCR
# Built from AWS's official aws-nitro-enclaves-sdk-c using Dockerfile.al2
FROM ghcr.io/0xktn/confidential-multi-agent-workflow:kmstool-v0.4.3 AS kmstool-base

# Final stage: Add Python and our application
FROM amazonlinux:2023

WORKDIR /app

# Copy kmstool binary and dependencies from base
COPY --from=kmstool-base /usr/bin/kmstool_enclave /usr/bin/kmstool_enclave_cli
COPY --from=kmstool-base /usr/lib64/libnsm.so /usr/lib64/
COPY --from=kmstool-base /etc/pki/tls/certs /etc/pki/tls/certs

# Install Python 3.11 and runtime dependencies
RUN dnf install -y python3.11 python3.11-pip && dnf clean all

# Install Python dependencies
RUN pip3.11 install --no-cache-dir cryptography boto3

# Copy our application
COPY app.py .
COPY run.sh .
RUN chmod +x run.sh /usr/bin/kmstool_enclave_cli

# Entrypoint
CMD ["/app/run.sh"]
