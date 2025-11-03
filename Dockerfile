# Multi-architecture Dockerfile for PLUMBUS backup server
# Supports ARM and x86 architectures (32-bit and 64-bit)
FROM python:3.11-slim

# Install required system packages for SSH and rsync
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    rsync \
    sshpass \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
