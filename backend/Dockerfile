FROM python:3.11-slim

WORKDIR /app

# Install security scanners and build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast, reliable SAT dependency resolution
RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system --no-cache --index-strategy unsafe-best-match -r requirements.txt

# Install scanners
RUN uv pip install --system --no-cache bandit pip-audit ruff black mypy pytest pytest-json-report

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
