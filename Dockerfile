FROM python:3.10.12

COPY . /workspace
RUN apt-get update && \
    apt-get install -y git && \
    pip install --upgrade pip && \
    pip install -r /workspace/requirements.txt

WORKDIR /workspace

CMD ["cat"]