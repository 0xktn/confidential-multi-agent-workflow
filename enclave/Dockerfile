# Attempt 22: Based on official AWS Dockerfile.al2
# https://github.com/aws/aws-nitro-enclaves-sdk-c/blob/main/containers/Dockerfile.al2

FROM public.ecr.aws/amazonlinux/amazonlinux:2 as builder

# Install build tools
RUN yum install -y \
    cmake3 \
    gcc \
    git \
    tar \
    make \
    gcc-c++ \
    go \
    ninja-build \
    && yum clean all

# Install Rust 1.71 (required for nsm-api)
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --profile minimal --default-toolchain 1.71

WORKDIR /tmp/crt-builder

# 1. aws-lc (crypto library)
RUN git clone --depth 1 -b v1.12.0 https://github.com/awslabs/aws-lc.git && \
    cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -GNinja \
    -DBUILD_TESTING=0 -S aws-lc -B aws-lc/build && \
    go env -w GOPROXY=direct && \
    cmake3 --build aws-lc/build --target install && \
    rm -rf aws-lc

# 2. s2n-tls
RUN git clone --depth 1 -b v1.3.46 https://github.com/aws/s2n-tls.git && \
    cmake3 -DCMAKE_PREFIX_PATH=/usr -DBUILD_TESTING=0 -DCMAKE_INSTALL_PREFIX=/usr \
    -S s2n-tls -B s2n-tls/build && \
    cmake3 --build s2n-tls/build --target install && \
    rm -rf s2n-tls

# 3. aws-c-common (CRITICAL: provides AwsFindPackage.cmake!)
RUN git clone --depth 1 -b v0.8.0 https://github.com/awslabs/aws-c-common.git && \
    cmake3 -DCMAKE_PREFIX_PATH=/usr -DBUILD_TESTING=0 -DCMAKE_INSTALL_PREFIX=/usr \
    -GNinja -S aws-c-common -B aws-c-common/build && \
    cmake3 --build aws-c-common/build --target install && \
    rm -rf aws-c-common

# 4. aws-c-sdkutils
RUN git clone --depth 1 -b v0.1.2 https://github.com/awslabs/aws-c-sdkutils.git && \
    cmake3 -DCMAKE_PREFIX_PATH=/usr -DBUILD_TESTING=0 -DCMAKE_INSTALL_PREFIX=/usr \
    -GNinja -S aws-c-sdkutils -B aws-c-sdkutils/build && \
    cmake3 --build aws-c-sdkutils/build --target install && \
    rm -rf aws-c-sdkutils

# 5. aws-c-cal
RUN git clone --depth 1 -b v0.5.18 https://github.com/awslabs/aws-c-cal.git && \
    cmake3 -DCMAKE_PREFIX_PATH=/usr -DBUILD_TESTING=0 -DCMAKE_INSTALL_PREFIX=/usr \
    -GNinja -S aws-c-cal -B aws-c-cal/build && \
    cmake3 --build aws-c-cal/build --target install && \
    rm -rf aws-c-cal

# 6. aws-c-io (VSOCK required for enclaves!)
RUN git clone --depth 1 -b v0.11.0 https://github.com/awslabs/aws-c-io.git && \
    cmake3 -DUSE_VSOCK=1 -DCMAKE_PREFIX_PATH=/usr -DBUILD_TESTING=0 \
    -DCMAKE_INSTALL_PREFIX=/usr -GNinja -S aws-c-io -B aws-c-io/build && \
    cmake3 --build aws-c-io/build --target install && \
    rm -rf aws-c-io

# 7. aws-c-compression
RUN git clone --depth 1 -b v0.2.14 https://github.com/awslabs/aws-c-compression.git && \
    cmake3 -DCMAKE_PREFIX_PATH=/usr -DBUILD_TESTING=0 -DCMAKE_INSTALL_PREFIX=/usr \
    -GNinja -S aws-c-compression -B aws-c-compression/build && \
    cmake3 --build aws-c-compression/build --target install && \
    rm -rf aws-c-compression

# 8. aws-c-http
RUN git clone --depth 1 -b v0.7.6 https://github.com/awslabs/aws-c-http.git && \
    cmake3 -DCMAKE_PREFIX_PATH=/usr -DBUILD_TESTING=0 -DCMAKE_INSTALL_PREFIX=/usr \
    -GNinja -S aws-c-http -B aws-c-http/build && \
    cmake3 --build aws-c-http/build --target install && \
    rm -rf aws-c-http

# 9. aws-c-auth
RUN git clone --depth 1 -b v0.6.15 https://github.com/awslabs/aws-c-auth.git && \
    cmake3 -DCMAKE_PREFIX_PATH=/usr -DBUILD_TESTING=0 -DCMAKE_INSTALL_PREFIX=/usr \
    -GNinja -S aws-c-auth -B aws-c-auth/build && \
    cmake3 --build aws-c-auth/build --target install && \
    rm -rf aws-c-auth

# 10. json-c
RUN git clone --depth 1 -b json-c-0.16-20220414 https://github.com/json-c/json-c.git && \
    cmake3 -DCMAKE_PREFIX_PATH=/usr -DBUILD_TESTING=0 -DCMAKE_INSTALL_PREFIX=/usr \
    -DBUILD_SHARED_LIBS=OFF -GNinja -S json-c -B json-c/build && \
    cmake3 --build json-c/build --target install && \
    rm -rf json-c

# 11. nsm-api (Rust library)
RUN git clone --depth 1 -b v0.4.0 https://github.com/aws/aws-nitro-enclaves-nsm-api.git && \
    source $HOME/.cargo/env && cd aws-nitro-enclaves-nsm-api && \
    cargo build --release -p nsm-lib && \
    mv target/release/libnsm.so /usr/lib64 && \
    mv target/release/nsm.h /usr/include && \
    cd .. && rm -rf aws-nitro-enclaves-nsm-api

# 12. aws-nitro-enclaves-sdk-c (the actual SDK)
RUN git clone --depth 1 -b v0.4.3 https://github.com/aws/aws-nitro-enclaves-sdk-c.git && \
    cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -GNinja \
    -S aws-nitro-enclaves-sdk-c -B aws-nitro-enclaves-sdk-c/build && \
    cmake3 --build aws-nitro-enclaves-sdk-c/build --target install && \
    rm -rf aws-nitro-enclaves-sdk-c

# Final stage: minimal runtime image
FROM public.ecr.aws/amazonlinux/amazonlinux:2

# Install runtime dependencies
RUN yum install -y python3 python3-pip findutils && yum clean all

# Copy built artifacts
COPY --from=builder /usr/lib64/libnsm.so /usr/lib64/libnsm.so
COPY --from=builder /usr/bin/kmstool_enclave_cli /usr/bin/kmstool_enclave_cli

# Copy application
WORKDIR /app
COPY app.py requirements.txt run.sh ./

# Setup Python environment
RUN python3 -m venv venv && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt

CMD ["./run.sh"]
