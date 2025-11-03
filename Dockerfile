# Multi-architecture Dockerfile for PLUMBUS backup server
# Supports ARM and x86 architectures (32-bit and 64-bit)
FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install all dependencies, build Python packages, then remove build dependencies
# This is done in one RUN command to minimize layer size
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-client \
        rsync \
        sshpass \
        gcc \
        libffi-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y gcc libffi-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . .

# Create data directory for database and backups
RUN mkdir -p /data/backups /data/db

# Expose port for web interface
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV DATA_DIR=/data

# Run the application
CMD ["python", "app.py"]
