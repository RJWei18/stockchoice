FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Taipei

WORKDIR /app

# Install system dependencies (tzdata for accurate cron timezones)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and default assets
COPY src/ /app/src/
COPY tests/ /app/tests/

# Create persistent data directory
RUN mkdir -p /app/data

CMD ["python", "src/main.py"]
