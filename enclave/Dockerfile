# Builder: Amazon Linux 2
FROM amazonlinux:2 AS builder

# Install build tools
RUN amazon-linux-extras install aws-nitro-enclaves-cli -y && \
    yum install -y \
    git \
    gcc \
    gcc-c++ \
    cmake \
    ninja-build \
    aws-nitro-enclaves-cli-devel \
    openssl-devel \
    pkgconfig \
    yum-utils \
    && yum clean all

# Install cmake3 (AL2 default cmake is too old)
RUN yum install -y cmake3 && \
    ln -sf /usr/bin/cmake3 /usr/bin/cmake

# Setup build environment
ENV INSTALL_PATH=/usr/local
ENV CMAKE_PREFIX_PATH=/usr:$INSTALL_PATH
ENV PKG_CONFIG_PATH=$INSTALL_PATH/lib/pkgconfig:$PKG_CONFIG_PATH

# 1. Build json-c from source (0.15 is stable)
# We disable Werror to avoid compilation issues on older GCC
RUN git clone --depth 1 -b json-c-0.15-20200726 https://github.com/json-c/json-c.git && \
    mkdir -p json-c/build && \
    cd json-c/build && \
    cmake3 .. \
    -DCMAKE_INSTALL_PREFIX=$INSTALL_PATH \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=OFF \
    -DBUILD_TESTING=OFF \
    && \
    make install && \
    cd ../.. && rm -rf json-c

# 2. Build SDK-C Application
RUN git clone --depth 1 -b v0.4.3 https://github.com/aws/aws-nitro-enclaves-sdk-c.git && \
    cmake3 -S aws-nitro-enclaves-sdk-c -B aws-nitro-enclaves-sdk-c/build -GNinja \
    -DCMAKE_INSTALL_PREFIX=$INSTALL_PATH \
    -DBUILD_TESTING=OFF \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=OFF \
    && \
    cmake3 --build aws-nitro-enclaves-sdk-c/build --target install && \
    rm -rf aws-nitro-enclaves-sdk-c

# Final Stage
FROM amazonlinux:2

# Runtime dependencies
RUN amazon-linux-extras install aws-nitro-enclaves-cli -y && \
    yum install -y \
    python3 \
    python3-pip \
    findutils \
    && yum clean all

# Copy artifact
COPY --from=builder /usr/local/bin/kmstool_enclave_cli /usr/bin/kmstool_enclave_cli

# Environment
WORKDIR /app
COPY app.py requirements.txt run.sh ./

# Setup Python environment
RUN python3 -m venv venv && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt

# Run
CMD ["./run.sh"]
