# GeneRisk — Backend Dockerfile
# Deploy this to Railway.app

FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    wget curl gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (Docker cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code
COPY backend/ ./backend/
COPY data/ ./data/
COPY .env.example .env

# Create data directories
RUN mkdir -p /app/data/chromadb /app/data/gwas_weights

# Setup ChromaDB knowledge base (runs during build)
RUN python data/setup_chromadb.py || echo "ChromaDB setup deferred to runtime"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s \
  CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI server
CMD ["uvicorn", "backend.cloud_worker.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
