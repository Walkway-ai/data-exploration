FROM python:3.10.12

# Set the environment variable for non-interactive installation
ENV CLOUD_SDK_VERSION=367.0.0
ENV DEBIAN_FRONTEND=noninteractive

# Copy requirements and source files
COPY requirements.txt /workspace/requirements.txt
COPY src /workspace/src

# Install dependencies and Google Cloud SDK
RUN apt-get update && \
    apt-get install -y git curl && \
    # Install pip dependencies
    pip install --upgrade pip && \
    pip install -r /workspace/requirements.txt && \
    # Download and install Google Cloud SDK
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    tar -xf google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    yes | ./google-cloud-sdk/install.sh && \
    yes | ./google-cloud-sdk/bin/gcloud components install gke-gcloud-auth-plugin && \
    # Clean up
    rm google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add gcloud to PATH
ENV PATH=/workspace/google-cloud-sdk/bin:$PATH

WORKDIR /workspace

CMD ["cat"]
