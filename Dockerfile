FROM python:3.10.12

COPY requirements.txt /workspace/requirements.txt
RUN apt-get update && \
    apt-get install -y git && \
    pip install --upgrade pip && \
    pip install -r /workspace/requirements.txt

WORKDIR /workspace

COPY src /workspace/src

CMD ["cat"]