FROM python:3.11-slim

# Prevents Python from writing .pyc files and buffers stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required for image processing packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       wget \
       git \
       ca-certificates \
       libglib2.0-0 \
       libsm6 \
       libxrender1 \
       libxext6 \
       libgl1 \
       ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies first (cache layer)
COPY requirements.txt ./requirements.txt

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy the backend source
COPY . /app

# Create a non-root user (optional but good practice)
RUN useradd --create-home appuser || true
RUN chown -R appuser:appuser /app
USER appuser

# Render (and many platforms) provide the port via the $PORT env var
ENV PORT=8000

EXPOSE 8000

# Use sh -c to allow ${PORT:-8000} fallback
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
