FROM python:3.12-slim

WORKDIR /app

# Install system deps for PDF/OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

ENTRYPOINT ["python", "-m", "mcp_server_convert"]
