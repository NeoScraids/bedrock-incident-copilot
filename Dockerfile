FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY src/ ./src/
COPY simulate_incident.py .

ENV PYTHONUNBUFFERED=1
ENV BEDROCK_MOCK=true

ENTRYPOINT ["python", "simulate_incident.py"]
CMD ["--scenario", "oom-killed"]
