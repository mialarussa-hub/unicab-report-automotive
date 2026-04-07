FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .

# Scrapers are invoked by n8n via HTTP; this runs a simple API
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8001"]
