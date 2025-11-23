# Inferno-AI Pentesting Sandbox
# Evidence-based tooling from analyzing 2,260 commands across 104 XBOW challenges
#
# Coverage: curl (1,463 uses), bash (636 uses), gobuster (15), ffuf (11), python3 (11), nodejs (3)
# This configuration covers 99% of actual tool usage observed in production CTF scans

FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install base system tools and dependencies
RUN apt-get update && apt-get install -y \
    # CRITICAL TOOLS (93% of command usage)
    curl \
    wget \
    ca-certificates \
    git \
    # Build essentials for compiling tools
    build-essential \
    # Python environment
    python3 \
    python3-pip \
    python3-venv \
    # Core utilities (bash is included in base image)
    coreutils \
    findutils \
    grep \
    sed \
    gawk \
    # Network utilities (3 uses of nc in logs)
    netcat-traditional \
    dnsutils \
    iputils-ping \
    # Port scanning (2 uses in logs)
    nmap \
    # Node.js for JS-heavy targets (3 uses in logs)
    nodejs \
    npm \
    # JSON parsing utility
    jq \
    # Directory enumeration (2 uses in logs)
    dirb \
    && rm -rf /var/lib/apt/lists/*

# Install Go for modern pentesting tools
# Required for gobuster (15 uses) and ffuf (11 uses) - HIGH PRIORITY
ARG TARGETARCH
ENV GO_VERSION=1.21.5

# Download correct Go binary for architecture
RUN ARCH=$(dpkg --print-architecture) && \
    wget -q https://go.dev/dl/go${GO_VERSION}.linux-${ARCH}.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-${ARCH}.tar.gz && \
    rm go${GO_VERSION}.linux-${ARCH}.tar.gz

# Set Go environment
ENV PATH="/usr/local/go/bin:/root/go/bin:${PATH}" \
    GOPATH="/root/go" \
    CGO_ENABLED=1

# Install HIGH PRIORITY enumeration tools (based on CTF log evidence)
# gobuster: 15 uses, ffuf: 11 uses
RUN go install github.com/OJ/gobuster/v3@latest && \
    go install github.com/ffuf/ffuf/v2@latest && \
    # Copy to system bin for global access
    cp /root/go/bin/* /usr/local/bin/

# Create Python virtual environment and install packages
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python security packages (11 python3 uses in logs)
RUN /opt/venv/bin/pip install --no-cache-dir \
    # Core HTTP clients
    requests \
    httpx \
    aiohttp \
    # HTML/XML parsing
    beautifulsoup4 \
    lxml \
    # Security libraries
    pyjwt \
    cryptography \
    # Utilities
    urllib3 \
    python-dotenv

# Download wordlists for enumeration tools
# Used by gobuster (15 uses), ffuf (11 uses), dirb (2 uses) = 28 total uses
RUN mkdir -p /usr/share/wordlists && \
    cd /usr/share/wordlists && \
    # Common paths wordlist
    wget -q https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt && \
    # Medium directories wordlist  
    wget -q https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/raft-medium-directories.txt && \
    # Large comprehensive wordlist
    wget -q https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/big.txt && \
    # API endpoints
    wget -q https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/api/api-endpoints.txt

# Set working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]
