FROM python:3.10.12

# Set up working directory
WORKDIR /workspace

# Copy requirements and source files
COPY requirements.txt /workspace/requirements.txt
COPY src /workspace/src

# Install dependencies
RUN apt-get update && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["cat"]
