FROM python:3.10.12

RUN apt-get update && apt-get install -y git

RUN git clone https://fabio-walkway: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@github.com/Walkway-ai/data-exploration.git /workspace && \
    pip install --upgrade pip && \
    pip install -r /workspace/requirements.txt

WORKDIR /workspace

CMD ["cat"]