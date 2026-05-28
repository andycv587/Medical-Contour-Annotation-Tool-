FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    libglib2.0-0 \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -e .[dev]

CMD ["python", "benchmarks/run_benchmark.py", "--config", "benchmarks/configs/synthetic_smoke.yaml", "--output", "results/synthetic_smoke"]
